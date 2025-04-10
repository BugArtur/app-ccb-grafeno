import requests
import pandas as pd
import streamlit as st
from datetime import datetime, date
import io
import re

# Sempre primeiro!
st.set_page_config(page_title="Grafeno CCBs exports", layout="wide")

# --- AUTENTICAÇÃO ---
PASSWORD = "Owl@2025"
if "authenticated" not in st.session_state:
    st.session_state.authenticated = False

if not st.session_state.authenticated:
    st.image("https://ynsyiedskcrbkvfomjuv.supabase.co/storage/v1/object/public/png%20email/LgVerde.png?t=2024-11-28T15%3A09%3A07.950Z", width=200)
    st.title("🔒 Login")
    password_input = st.text_input("Digite a senha:", type="password")
    if password_input == PASSWORD:
        st.session_state.authenticated = True
        st.rerun()
    elif password_input:
        st.error("Senha incorreta. Tente novamente.")
else:
    st.image("https://ynsyiedskcrbkvfomjuv.supabase.co/storage/v1/object/public/png%20email/LgVerde.png?t=2024-11-28T15%3A09%3A07.950Z", width=200)
    st.title("📄 Relatório de CCBs - Grafeno")

    with st.sidebar:
        st.header("Autenticação e Filtros")
        api_key = st.text_input("API Key", type="password")
        date_from = st.date_input("Data inicial")
        date_to = st.date_input("Data final")
        fetch_button = st.button("Buscar dados")
        fetch_all_button = st.button("Buscar todas as CCBs")

    BASE_URL = "https://apis.grafeno.digital/laas/v1/credits"

    def fetch_installments(api_key, credit_id):
        url = f"https://apis.grafeno.digital/laas/v1/credits/{credit_id}/installments"
        headers = {
            "Authorization": api_key,
            "accept": "application/json",
            "User-Agent": "Mozilla/5.0"
        }
        response = requests.get(url, headers=headers)
        if response.status_code == 200:
            return response.json()
        return []

    def fetch_all_data(api_key, date_from=None, date_to=None):
        all_results = []
        page = 1
        headers = {
            "Authorization": api_key,
            "accept": "application/json",
            "User-Agent": "Mozilla/5.0"
        }
        while True:
            params = {
                "type": "ccb",
                "page": page,
                "limit": 100
            }
            response = requests.get(BASE_URL, headers=headers, params=params)
            if response.status_code != 200:
                st.error(f"Erro ao buscar dados: {response.status_code}")
                return []

            data = response.json().get("content", [])
            if not data:
                break

            all_results.extend(data)
            page += 1

        if date_from or date_to:
            all_results = [d for d in all_results if date_filter(d, date_from, date_to)]

        return all_results

    def date_filter(entry, date_from, date_to):
        created_at = datetime.strptime(entry.get("created_at"), "%Y-%m-%dT%H:%M:%S.%fZ")
        if date_from and created_at < date_from:
            return False
        if date_to and created_at > date_to:
            return False
        return True

    def format_cpf_cnpj(value):
        value = re.sub(r"\D", "", value)
        if len(value) == 11:
            return f"{value[:3]}.{value[3:6]}.{value[6:9]}-{value[9:]}"
        elif len(value) == 14:
            return f"{value[:2]}.{value[2:5]}.{value[5:8]}/{value[8:12]}-{value[12:]}"
        return value

    def format_currency(value):
        try:
            return f"R$ {float(value):,.2f}".replace(",", "v").replace(".", ",").replace("v", ".")
        except:
            return value

    def parse_data(data):
        rows = []
        for item in data:
            ident = item.get("debtor", {}).get("identification")
            formatted_ident = format_cpf_cnpj(ident) if ident else ""

            try:
                valor_liquido = float(item.get("value", 0))
                taxa = float(item.get("tax_percentage", 0)) / 100
                parcelas = int(item.get("installments_quantity", 1))
                valor_total = valor_liquido * ((1 + taxa) ** parcelas)
            except Exception:
                valor_total = "Erro"

            # Buscar e calcular parcelas
            installments = fetch_installments(api_key, item.get("id"))
            total_amortization = sum(float(i.get("amortization", 0)) for i in installments)
            total_interest = sum(float(i.get("interest_value", 0)) for i in installments)
            parcela_valor = installments[0].get("total_value") if installments else 0

            rows.append({
                
                "Data de Criação": datetime.strptime(item.get("created_at"), "%Y-%m-%dT%H:%M:%S.%fZ").strftime("%d/%m/%Y") if item.get("created_at") else "",
                "CCB": item.get("ccb_number"),
                "Nome": item.get("debtor", {}).get("name"),
                "CPF/CNPJ": formatted_ident,
                "Valor Liquido": format_currency(item.get("value")),
                "Parcelas": item.get("installments_quantity"),
                "Taxa": f"{item.get("tax_percentage", 0)}%",
                "Primeira Parcela": datetime.strptime(item.get("first_installment_date"), "%Y-%m-%d").strftime("%d/%m/%Y") if item.get("first_installment_date") else "",
                "Status": item.get("status"),
                "Total desembolsado": format_currency(total_amortization),
                "Total Juros": format_currency(total_interest),
                "Valor da Parcela": format_currency(parcela_valor),
                "Última Parcela": datetime.strptime(installments[-1].get("due_date"), "%Y-%m-%dT%H:%M:%S.%fZ").strftime("%d/%m/%Y") if installments else ""
            })
        return pd.DataFrame(rows)

    if (fetch_button or fetch_all_button) and api_key:
        if fetch_all_button:
            date_from = datetime(2024, 1, 1)
            date_to = datetime.today()

        with st.spinner("Buscando dados da API da Grafeno..."):
            df_raw = fetch_all_data(
                api_key,
                datetime.combine(date_from, datetime.min.time()) if date_from else None,
                datetime.combine(date_to, datetime.max.time()) if date_to else None
            )
            df = parse_data(df_raw)
            st.success(f"Foram encontrados {len(df)} registros.")

            st.dataframe(df)

            output = io.BytesIO()
            with pd.ExcelWriter(output, engine='openpyxl') as writer:
                df.to_excel(writer, index=False)
            st.download_button(
                label="📥 Baixar Excel",
                data=output.getvalue(),
                file_name="grafeno_ccbs.xlsx",
                mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
            )
    elif (fetch_button or fetch_all_button) and not api_key:
        st.warning("Por favor, informe a API Key.")
