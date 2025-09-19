import streamlit as st
import pandas as pd
import datetime
import os

# Arquivo da base de dados
DB_FILE = "dados tratados.csv"

# Carregar base existente ou criar nova
if os.path.exists(DB_FILE):
    df = pd.read_csv(DB_FILE)
else:
    df = pd.DataFrame(columns=["Data", "Motivo", "Destinatario", "Método", "Parcelas", "Valor Total", "Parcela", "Valor", "Mes/Ano", "Ano", "Mes"])

st.title("Controle de Compras Parceladas")

st.header("Cadastro de nova compra")
with st.form("nova_compra"):
    motivo = st.text_input("Motivo da compra")
    destinatario = st.text_input("Pra quem é o pagamento")
    metodo = st.text_input("Método")
    parcelas = st.number_input("Quantidade de parcelas", min_value=1, step=1)
    valor_total = st.number_input("Valor total (R$)", min_value=0.0, format="%.2f")
    enviar = st.form_submit_button("Adicionar")

if enviar:
    if motivo and destinatario and metodo and parcelas > 0 and valor_total > 0:
        valor_parcela = round(valor_total / parcelas, 2)
        hoje = datetime.date.today()

        novas_linhas = []
        for i in range(parcelas):
            mes = (hoje.month + i - 1) % 12 + 1
            ano = hoje.year + ((hoje.month + i - 1) // 12)
            mes_ano = f"{mes:02d}/{ano}"

            novas_linhas.append({
                "Motivo": motivo,
                "Destinatário": destinatario,
                "Método": metodo,
                "Parcelas": parcelas,
                "Valor Total": valor_total,
                "Parcela": i+1,
                "Valor": valor_parcela,
                "Mes/Ano": mes_ano,
                "Ano": ano,
                "Mes": mes
            })

        df = pd.concat([df, pd.DataFrame(novas_linhas)], ignore_index=True)
        df.to_csv(DB_FILE, index=False)
        st.success("Compra registrada com sucesso!")
    else:
        st.error("Preencha todos os campos corretamente.")

st.header("Visualização das parcelas")

# Mostrar tabela completa
st.dataframe(df)

if not df.empty:
    # Resumo geral de todos os anos
    resumo_geral = df.groupby(["Ano", "Mes"])["Valor"].sum().reset_index()
    resumo_geral = resumo_geral.sort_values(["Ano", "Mes"])
    resumo_geral["Mes/Ano"] = resumo_geral["Mes"].astype(str).str.zfill(2) + "/" + resumo_geral["Ano"].astype(str)

    st.subheader("Resumo geral por mês (todos os anos)")
    st.table(resumo_geral[["Mes/Ano", "Valor"]])
    st.line_chart(data=resumo_geral, x="Mes/Ano", y="Valor")

    # Filtro por ano
    anos_disponiveis = sorted(df["Ano"].unique())
    ano_filtro = st.selectbox("Selecione o ano para detalhar", options=anos_disponiveis)

    df_filtrado = df[df["Ano"] == ano_filtro]

    resumo = df_filtrado.groupby(["Ano", "Mes"])["Valor"].sum().reset_index()
    resumo = resumo.sort_values(["Ano", "Mes"])
    resumo["Mes/Ano"] = resumo["Mes"].astype(str).str.zfill(2) + "/" + resumo["Ano"].astype(str)

    st.subheader(f"Resumo por mês - {ano_filtro}")
    st.table(resumo[["Mes/Ano", "Valor"]])
    st.line_chart(data=resumo, x="Mes/Ano", y="Valor")

    # Parcelas do mês atual
    hoje = datetime.date.today()
    mes_atual = hoje.month
    ano_atual = hoje.year

    parcelas_mes = df[(df["Ano"] == ano_atual) & (df["Mes"] == mes_atual)]

    if not parcelas_mes.empty:
        st.subheader("Parcelas deste mês")
        for _, row in parcelas_mes.iterrows():
            st.write(f"📌 {row['Motivo']} - Parcela {row['Parcela']}/{row['Parcelas']} | Valor: R$ {row['Valor']:.2f} | Método: {row['Método']} | Pra quem: {row['Destinatário']}")

        total_mes = parcelas_mes["Valor"].sum()
        st.markdown(f"### 💰 Total a pagar neste mês: R$ {total_mes:.2f}")
    else:
        st.info("Nenhuma parcela para este mês.")

    # Previsão dos próximos meses
    st.header("Previsão de parcelas futuras")
    meses_futuros = df[(df["Ano"] > ano_atual) | ((df["Ano"] == ano_atual) & (df["Mes"] > mes_atual))]

    if not meses_futuros.empty:
        previsao = meses_futuros.groupby(["Ano", "Mes"])["Valor"].sum().reset_index()
        previsao = previsao.sort_values(["Ano", "Mes"])
        previsao["Mes/Ano"] = previsao["Mes"].astype(str).str.zfill(2) + "/" + previsao["Ano"].astype(str)

        st.subheader("Totais dos próximos meses")
        st.table(previsao[["Mes/Ano", "Valor"]])
        st.line_chart(data=previsao, x="Mes/Ano", y="Valor")

        st.subheader("Detalhes das parcelas futuras")
        for _, row in meses_futuros.iterrows():
            st.write(f"📌 {row['Mes/Ano']} - {row['Motivo']} - Parcela {row['Parcela']}/{row['Parcelas']} | Valor: R$ {row['Valor']:.2f} | Método: {row['Método']} | Pra quem: {row['Destinatário']}")
    else:
        st.info("Não há parcelas futuras registradas.")
