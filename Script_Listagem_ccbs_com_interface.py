# import requests
# import pandas as pd
# import streamlit as st
# from datetime import datetime, date
# import io
# import re

# # Sempre primeiro!
# st.set_page_config(page_title="Grafeno CCBs exports", layout="wide")

# # --- AUTENTICAÇÃO ---
# PASSWORD = "Owl@2025"
# if "authenticated" not in st.session_state:
#     st.session_state.authenticated = False

# if not st.session_state.authenticated:
#     st.image("https://ynsyiedskcrbkvfomjuv.supabase.co/storage/v1/object/public/png%20email/LgVerde.png?t=2024-11-28T15%3A09%3A07.950Z", width=200)
#     st.title("🔒 Login")
#     password_input = st.text_input("Digite a senha:", type="password")
#     if password_input == PASSWORD:
#         st.session_state.authenticated = True
#         st.rerun()
#     elif password_input:
#         st.error("Senha incorreta. Tente novamente.")
# else:
#     st.image("https://ynsyiedskcrbkvfomjuv.supabase.co/storage/v1/object/public/png%20email/LgVerde.png?t=2024-11-28T15%3A09%3A07.950Z", width=200)
#     st.title("📄 Relatório de CCBs - Grafeno")

#     with st.sidebar:
#         st.header("Autenticação e Filtros")
#         api_key = st.text_input("API Key", type="password")
#         date_from = st.date_input("Data inicial")
#         date_to = st.date_input("Data final")
#         fetch_button = st.button("Buscar dados")
#         fetch_all_button = st.button("Buscar todas as CCBs")

#     BASE_URL = "https://apis.grafeno.digital/laas/v1/credits"

#     def fetch_installments(api_key, credit_id):
#         url = f"https://apis.grafeno.digital/laas/v1/credits/{credit_id}/installments"
#         headers = {
#             "Authorization": api_key,
#             "accept": "application/json",
#             "User-Agent": "Mozilla/5.0"
#         }
#         response = requests.get(url, headers=headers)
#         if response.status_code == 200:
#             return response.json()
#         return []

#     def fetch_all_data(api_key, date_from=None, date_to=None):
#         all_results = []
#         page = 1
#         headers = {
#             "Authorization": api_key,
#             "accept": "application/json",
#             "User-Agent": "Mozilla/5.0"
#         }
#         while True:
#             params = {
#                 "type": "ccb",
#                 "page": page,
#                 "limit": 100
#             }
#             try:
#                 response = requests.get(BASE_URL, headers=headers, params=params, timeout=60)
#             except requests.exceptions.ReadTimeout:
#                 st.error("A requisição demorou muito e foi interrompida. Tente novamente mais tarde.")
#                 return []
#             if response.status_code != 200:
#                 st.error(f"Erro ao buscar dados: {response.status_code}")
#                 return []

#             data = response.json().get("content", [])
#             if not data:
#                 break

#             all_results.extend(data)
#             page += 1

#         if date_from or date_to:
#             all_results = [d for d in all_results if date_filter(d, date_from, date_to)]

#         return all_results

#     def date_filter(entry, date_from, date_to):
#         created_at = datetime.strptime(entry.get("created_at"), "%Y-%m-%dT%H:%M:%S.%fZ")
#         if date_from and created_at < date_from:
#             return False
#         if date_to and created_at > date_to:
#             return False
#         return True

#     def format_cpf_cnpj(value):
#         value = re.sub(r"\D", "", value)
#         if len(value) == 11:
#             return f"{value[:3]}.{value[3:6]}.{value[6:9]}-{value[9:]}"
#         elif len(value) == 14:
#             return f"{value[:2]}.{value[2:5]}.{value[5:8]}/{value[8:12]}-{value[12:]}"
#         return value

#     def traduzir_status(status):
#         mapa = {
#             "draft": "Rascunho",
#             "confirmed": "Confirmado",
#             "admin_analysis": "Análise Administrativa",
#             "cancelled": "Cancelado",
#             "bookkeeper_analysis": "Análise Contábil",
#             "banker": "Aguardando Banco",
#             "analyze": "Em Análise",
#             "returned": "Devolvido",
#             "refused": "Recusado",
#             "signature": "Aguardando Assinatura",
#             "signed": "Assinado",
#             "assignment_process": "Processo de Cessão",
#             "disbursed": "Desembolsado"
#         }
#         return mapa.get(status, status)

#     def format_currency(value):
#         try:
#             return f"R$ {float(value):,.2f}".replace(",", "v").replace(".", ",").replace("v", ".")
#         except:
#             return value

#     def parse_data(data):
#         rows = []
#         for item in data:
#             debtor = item.get("debtor")
#             if isinstance(debtor, dict):
#                 ident = debtor.get("identification")
#             else:
#                 ident = ""
#             formatted_ident = format_cpf_cnpj(ident) if ident else ""

#             try:
#                 valor_liquido = float(item.get("value", 0))
#                 taxa = float(item.get("tax_percentage", 0)) / 100
#                 parcelas = int(item.get("installments_quantity", 1))
#                 valor_total = valor_liquido * ((1 + taxa) ** parcelas)
#             except Exception:
#                 valor_total = "Erro"

#             installments = fetch_installments(api_key, item.get("id"))
#             total_amortization = sum(float(i.get("amortization", 0)) for i in installments)
#             total_interest = sum(float(i.get("interest_value", 0)) for i in installments)
#             parcela_valor = installments[0].get("total_value") if installments else 0

#             rows.append({
#                 "id": item.get("id"),
#                 "Data de Criação": datetime.strptime(item.get("created_at"), "%Y-%m-%dT%H:%M:%S.%fZ").strftime("%d/%m/%Y") if item.get("created_at") else "",
#                 "CCB": item.get("ccb_number"),
#                 "Nome": debtor.get("name") if isinstance(debtor, dict) else "",
#                 "CPF/CNPJ": formatted_ident,
#                 "Valor Liquido": format_currency(item.get("value")),
#                 "Parcelas": item.get("installments_quantity"),
#                 "Taxa": f"{item.get('tax_percentage', 0)}%",
#                 "Primeira Parcela": datetime.strptime(item.get("first_installment_date"), "%Y-%m-%d").strftime("%d/%m/%Y") if item.get("first_installment_date") else "",
#                 "Status": traduzir_status(item.get("status")),
#                 "Total desembolsado": format_currency(total_amortization),
#                 "Total Juros": format_currency(total_interest),
#                 "Valor da Parcela": format_currency(parcela_valor),
#                 "Última Parcela": datetime.strptime(installments[-1].get("due_date"), "%Y-%m-%dT%H:%M:%S.%fZ").strftime("%d/%m/%Y") if installments else ""
#             })
#         return pd.DataFrame(rows)

#     df = None
#     if (fetch_button or fetch_all_button) and api_key:
#         if fetch_all_button:
#             date_from = datetime(2024, 1, 1)
#             date_to = datetime.today()

#         with st.spinner("Buscando dados da API da Grafeno..."):
#             df_raw = fetch_all_data(
#                 api_key,
#                 datetime.combine(date_from, datetime.min.time()) if date_from else None,
#                 datetime.combine(date_to, datetime.max.time()) if date_to else None
#             )
#             df = pd.DataFrame()
#             st.session_state.df_raw = df_raw
#             progress_bar = st.progress(0)
#             progress_text = st.empty()
#             total = len(df_raw)
#             start_time = datetime.now()
#             for i, item in enumerate(df_raw):
#                 parsed = parse_data([item])
#                 df = pd.concat([df, parsed], ignore_index=True)
#                 st.session_state.df = df
#                 progress = (i + 1) / total
#                 elapsed = (datetime.now() - start_time).total_seconds()
#                 est_total = (elapsed / (i + 1)) * total
#                 est_remaining = max(est_total - elapsed, 0)
#                 progress_bar.progress(progress)
#                 progress_text.text(f"Progresso: {int(progress * 100)}% | Tempo restante estimado: {int(est_remaining)}s")
#             progress_bar.empty()
#     elif not fetch_button and not fetch_all_button:
#         df = st.session_state.get("df")

#     if df is not None and not df.empty:
#         st.dataframe(df)

#         output = io.BytesIO()
#         with pd.ExcelWriter(output, engine='openpyxl') as writer:
#             df.to_excel(writer, index=False)
#         st.download_button(
#             label="📥 Baixar planilha geral das CCBs",
#             data=output.getvalue(),
#             file_name="grafeno_ccbs.xlsx",
#             mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
#         )

#         st.subheader("🔍 Buscar parcelas por número de CCB")
#         ccb_search = st.text_input("Digite o número da CCB", key="ccb_search")
#         if ccb_search:
#             ccb_row = df[df['CCB'] == ccb_search]
#             if not ccb_row.empty:
#                 selected_id = ccb_row.iloc[0]['id']
#                 installments = fetch_installments(api_key, selected_id)
#                 if installments:
#                     nome = ccb_row.iloc[0]['Nome']
#                     documento = ccb_row.iloc[0]['CPF/CNPJ']
#                     tabela = pd.DataFrame([{
#                         "Parcela": i + 1,
#                         "Vencimento": datetime.strptime(inst['due_date'], "%Y-%m-%dT%H:%M:%S.%fZ").strftime("%d/%m/%Y"),
#                         "Amortização": format_currency(inst['amortization']),
#                         "Juros": format_currency(inst['interest_value']),
#                         "Valor Parcela": format_currency(inst['total_value'])
#                     } for i, inst in enumerate(installments)])
#                     st.write(f"📄 Parcelas para CCB {ccb_search} - {nome} ({documento}):")
#                     st.dataframe(tabela, use_container_width=True)

#                     output = io.BytesIO()
#                     with pd.ExcelWriter(output, engine='openpyxl') as writer:
#                         tabela.to_excel(writer, index=False)
#                     st.download_button(
#                         label="📥 Baixar parcelas em Excel",
#                         data=output.getvalue(),
#                         file_name=f"parcelas_ccb_{ccb_search}.xlsx",
#                         mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
#                     )
#                 else:
#                     st.info("Nenhuma parcela encontrada para esta CCB.")
#             else:
#                 st.warning("CCB não encontrada na base carregada.")

#     elif (fetch_button or fetch_all_button) and not api_key:
#         st.warning("Por favor, informe a API Key.")
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
            try:
                response = requests.get(BASE_URL, headers=headers, params=params, timeout=60)
            except requests.exceptions.ReadTimeout:
                st.error("A requisição demorou muito e foi interrompida. Tente novamente mais tarde.")
                return []
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

    def traduzir_status(status):
        mapa = {
            "draft": "Rascunho",
            "confirmed": "Confirmado",
            "admin_analysis": "Análise Administrativa",
            "cancelled": "Cancelado",
            "bookkeeper_analysis": "Análise Contábil",
            "banker": "Aguardando Banco",
            "analyze": "Em Análise",
            "returned": "Devolvido",
            "refused": "Recusado",
            "signature": "Aguardando Assinatura",
            "signed": "Assinado",
            "assignment_process": "Processo de Cessão",
            "disbursed": "Desembolsado"
        }
        return mapa.get(status, status)

    def format_currency(value):
        try:
            return f"R$ {float(value):,.2f}".replace(",", "v").replace(".", ",").replace("v", ".")
        except:
            return value

    def parse_data(data):
        rows = []
        for item in data:
            debtor = item.get("debtor")
            if isinstance(debtor, dict):
                ident = debtor.get("identification")
            else:
                ident = ""
            formatted_ident = format_cpf_cnpj(ident) if ident else ""

            try:
                valor_liquido = float(item.get("value", 0))
                taxa = float(item.get("tax_percentage", 0)) / 100
                parcelas = int(item.get("installments_quantity", 1))
                valor_total = valor_liquido * ((1 + taxa) ** parcelas)
            except Exception:
                valor_total = "Erro"

            installments = fetch_installments(api_key, item.get("id"))
            total_amortization = sum(float(i.get("amortization", 0)) for i in installments)
            total_interest = sum(float(i.get("interest_value", 0)) for i in installments)
            parcela_valor = installments[0].get("total_value") if installments else 0

            rows.append({
                "id": item.get("id"),
                "Data de Criação": datetime.strptime(item.get("created_at"), "%Y-%m-%dT%H:%M:%S.%fZ").strftime("%d/%m/%Y") if item.get("created_at") else "",
                "CCB": item.get("ccb_number"),
                "Nome": debtor.get("name") if isinstance(debtor, dict) else "",
                "CPF/CNPJ": formatted_ident,
                "Valor Liquido": format_currency(item.get("value")),
                "Parcelas": item.get("installments_quantity"),
                "Taxa": f"{item.get('tax_percentage', 0)}%",
                "Primeira Parcela": datetime.strptime(item.get("first_installment_date"), "%Y-%m-%d").strftime("%d/%m/%Y") if item.get("first_installment_date") else "",
                "Status": traduzir_status(item.get("status")),
                "Total desembolsado": format_currency(total_amortization),
                "Total Juros": format_currency(total_interest),
                "Valor da Parcela": format_currency(parcela_valor),
                "Última Parcela": datetime.strptime(installments[-1].get("due_date"), "%Y-%m-%dT%H:%M:%S.%fZ").strftime("%d/%m/%Y") if installments else ""
            })
        return pd.DataFrame(rows)

    df = None
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
            df = pd.DataFrame()
            st.session_state.df_raw = df_raw
            progress_bar = st.progress(0)
            progress_text = st.empty()
            total = len(df_raw)
            start_time = datetime.now()
            for i, item in enumerate(df_raw):
                parsed = parse_data([item])
                df = pd.concat([df, parsed], ignore_index=True)
                st.session_state.df = df
                progress = (i + 1) / total
                elapsed = (datetime.now() - start_time).total_seconds()
                est_total = (elapsed / (i + 1)) * total
                est_remaining = max(est_total - elapsed, 0)
                progress_bar.progress(progress)
                progress_text.text(f"Progresso: {int(progress * 100)}% | Tempo restante estimado: {int(est_remaining)}s")
            progress_bar.empty()
    elif not fetch_button and not fetch_all_button:
        df = st.session_state.get("df")

    if df is not None and not df.empty:
        st.markdown("### 📊 Indicadores: empréstimos desembolsados com sucesso")

        # KPIs gerais
        df_desembolsado = df[df['Status'] == 'Desembolsado']
        total_ccbs = len(df_desembolsado)
        total_liquido = sum(float(str(v).replace('R$','').replace('.','').replace(',','.')) for v in df_desembolsado['Valor Liquido'])
        total_desembolsado = sum(float(str(v).replace('R$','').replace('.','').replace(',','.')) for v in df_desembolsado['Total desembolsado'])
        total_juros = sum(float(str(v).replace('R$','').replace('.','').replace(',','.')) for v in df_desembolsado['Total Juros'])

        col1, col2, col3, col4 = st.columns(4)
        col1.metric("Total de CCBs", total_ccbs)
        col2.metric("Valor Líquido Total", format_currency(total_liquido))
        col3.metric("Total Desembolsado", format_currency(total_desembolsado))
        col4.metric("Total de Juros", format_currency(total_juros))

        st.dataframe(df)

        output = io.BytesIO()
        with pd.ExcelWriter(output, engine='openpyxl') as writer:
            df.to_excel(writer, index=False)
        st.download_button(
            label="📥 Baixar planilha geral das CCBs",
            data=output.getvalue(),
            file_name="grafeno_ccbs.xlsx",
            mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
        )

        st.subheader("🔍 Buscar parcelas por número de CCB")
        ccb_search = st.text_input("Digite o número da CCB", key="ccb_search")
        if ccb_search:
            ccb_row = df[df['CCB'] == ccb_search]
            if not ccb_row.empty:
                selected_id = ccb_row.iloc[0]['id']
                installments = fetch_installments(api_key, selected_id)
                if installments:
                    nome = ccb_row.iloc[0]['Nome']
                    documento = ccb_row.iloc[0]['CPF/CNPJ']
                    # KPIs
                    total_parcelas = len(installments)
                    total_amortizacao = sum(float(i.get("amortization", 0)) for i in installments)
                    total_juros = sum(float(i.get("interest_value", 0)) for i in installments)
                    total_pago = sum(float(i.get("total_value", 0)) for i in installments)

                    col1, col2, col3, col4 = st.columns(4)
                    col1.metric("Parcelas", total_parcelas)
                    col2.metric("Total Amortização", format_currency(total_amortizacao))
                    col3.metric("Total Juros", format_currency(total_juros))
                    col4.metric("Total a Pagar", format_currency(total_pago))

                    tabela = pd.DataFrame([{
                        "Parcela": i + 1,
                        "Vencimento": datetime.strptime(inst['due_date'], "%Y-%m-%dT%H:%M:%S.%fZ").strftime("%d/%m/%Y"),
                        "Amortização": format_currency(inst['amortization']),
                        "Juros": format_currency(inst['interest_value']),
                        "Valor Parcela": format_currency(inst['total_value'])
                    } for i, inst in enumerate(installments)])
                    st.write(f"📄 Parcelas para CCB {ccb_search} - {nome} ({documento}):")
                    st.dataframe(tabela, use_container_width=True)

                    output = io.BytesIO()
                    with pd.ExcelWriter(output, engine='openpyxl') as writer:
                        tabela.to_excel(writer, index=False)
                    st.download_button(
                        label="📥 Baixar parcelas em Excel",
                        data=output.getvalue(),
                        file_name=f"parcelas_ccb_{ccb_search}.xlsx",
                        mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
                    )
                else:
                    st.info("Nenhuma parcela encontrada para esta CCB.")
            else:
                st.warning("CCB não encontrada na base carregada.")

    elif (fetch_button or fetch_all_button) and not api_key:
        st.warning("Por favor, informe a API Key.")
