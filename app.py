import streamlit as st
import pandas as pd
import datetime
import os

# Configuração da página (DEVE ser a primeira chamada do Streamlit)
st.set_page_config(layout="wide")

# Arquivo da base de dados
DB_FILE = "dados tratados x.csv"

# Carregar base existente ou criar nova
if os.path.exists(DB_FILE):
    df = pd.read_csv(DB_FILE)
    # garantir tipos
    if "Ano" in df.columns:
        df["Ano"] = df["Ano"].astype(int)
    if "Mes" in df.columns:
        df["Mes"] = df["Mes"].astype(int)
    if "Valor" in df.columns:
        df["Valor"] = pd.to_numeric(df["Valor"], errors="coerce").fillna(0.0)
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
        # valor base por parcela (arredondado)
        valor_parcela_base = round(valor_total / parcelas, 2)
        hoje = datetime.date.today()

        novas_linhas = []
        for i in range(parcelas):
            # primeira parcela passa a ser NO PRÓXIMO MÊS
            mes = ((hoje.month + i) % 12) + 1
            ano = hoje.year + ((hoje.month + i) // 12)
            mes_ano = f"{mes:02d}/{ano}"

            if i < parcelas - 1:
                valor_parcela = valor_parcela_base
            else:
                valor_parcela = round(valor_total - valor_parcela_base * (parcelas - 1), 2)

            novas_linhas.append({
                "Data": hoje.strftime("%d/%m/%Y"),
                "Motivo": motivo,
                "Destinatário": destinatario,
                "Método": metodo,
                "Parcelas": parcelas,
                "Valor Total": valor_total,
                "Parcela": i + 1,
                "Valor": valor_parcela,
                "Mes/Ano": mes_ano,
                "Ano": ano,
                "Mes": mes
            })

        df = pd.concat([df, pd.DataFrame(novas_linhas)], ignore_index=True)
        df.to_csv(DB_FILE, index=False)
        st.success("Compra registrada com sucesso! (primeira parcela no mês seguinte)")
    else:
        st.error("Preencha todos os campos corretamente.")

st.header("Visualização das parcelas")

# Mostrar tabela completa
st.dataframe(df)

if not df.empty:
    # --- Organização em abas ---
    aba1, aba2, aba3, aba4, aba5 = st.tabs(["📊 Resumo Geral", "📅 Previsão Futuras", "💳 Métodos de Pagamento", "📌 Parcelas do Mês", "🧮 Simulação de Parcelas"])

    with aba1:
        st.subheader("Resumo geral por mês (todos os anos)")
        resumo_geral = df.groupby(["Ano", "Mes"])["Valor"].sum().reset_index()
        resumo_geral = resumo_geral.sort_values(["Ano", "Mes"])
        resumo_geral["Mes/Ano"] = resumo_geral["Mes"].astype(str).str.zfill(2) + "/" + resumo_geral["Ano"].astype(str)

        st.table(resumo_geral[["Mes/Ano", "Valor"]])
        st.line_chart(data=resumo_geral, x="Mes/Ano", y="Valor")

    with aba2:
        st.subheader("Previsão de parcelas futuras")
        hoje = datetime.date.today()
        mes_atual = hoje.month
        ano_atual = hoje.year

        meses_futuros = df[(df["Ano"] > ano_atual) | ((df["Ano"] == ano_atual) & (df["Mes"] > mes_atual))]

        if not meses_futuros.empty:
            # filtro de mês
            meses_disponiveis = meses_futuros[["Ano", "Mes"]].drop_duplicates().sort_values(["Ano", "Mes"])
            meses_disponiveis["Mes/Ano"] = meses_disponiveis["Mes"].astype(str).str.zfill(2) + "/" + meses_disponiveis["Ano"].astype(str)
            mes_escolhido = st.selectbox("Selecione o mês para visualizar", meses_disponiveis["Mes/Ano"])

            ano_filtro = int(mes_escolhido.split("/")[1])
            mes_filtro = int(mes_escolhido.split("/")[0])

            meses_futuros_filtrado = meses_futuros[(meses_futuros["Ano"] == ano_filtro) & (meses_futuros["Mes"] == mes_filtro)]

            previsao = meses_futuros.groupby(["Ano", "Mes"])["Valor"].sum().reset_index()
            previsao = previsao.sort_values(["Ano", "Mes"])
            previsao["Mes/Ano"] = previsao["Mes"].astype(str).str.zfill(2) + "/" + previsao["Ano"].astype(str)

            st.subheader("Totais dos próximos meses")
            st.table(previsao[["Mes/Ano", "Valor"]])
            st.line_chart(data=previsao, x="Mes/Ano", y="Valor")

            st.subheader(f"Detalhes das parcelas em {mes_escolhido}")
            for _, row in meses_futuros_filtrado.iterrows():
                st.write(f"📌 {row['Mes/Ano']} - {row['Motivo']} - Parcela {row['Parcela']}/{row['Parcelas']} | Valor: R$ {row['Valor']:.2f} | Método: {row['Método']}")

            total_mes_filtro = meses_futuros_filtrado["Valor"].sum()
            st.markdown(f"### 💰 Total a pagar neste mês: R$ {total_mes_filtro:.2f}")
        else:
            st.info("Não há parcelas futuras registradas.")

    with aba3:
        st.subheader("Distribuição por Método de Pagamento ao longo do tempo")
        resumo_metodo_mes = df.groupby(["Mes/Ano", "Método"])["Valor"].sum().reset_index()
        resumo_metodo_mes = resumo_metodo_mes.pivot(index="Método", columns="Mes/Ano", values="Valor").fillna(0)
        st.bar_chart(resumo_metodo_mes.transpose())

    with aba4:
        hoje = datetime.date.today()
        mes_atual = hoje.month
        ano_atual = hoje.year

        parcelas_mes = df[(df["Ano"] == ano_atual) & (df["Mes"] == mes_atual)]

        if not parcelas_mes.empty:
            st.subheader("Parcelas deste mês")
            for _, row in parcelas_mes.iterrows():
                st.write(f"📌 {row['Motivo']} - Parcela {row['Parcela']}/{row['Parcelas']} | Valor: R$ {row['Valor']:.2f} | Método: {row['Método']}")

            total_mes = parcelas_mes["Valor"].sum()
            st.markdown(f"### 💰 Total a pagar neste mês: R$ {total_mes:.2f}")

            # gráfico de métodos apenas do mês atual
            st.subheader("Distribuição por Método de Pagamento neste mês")
            resumo_metodo_mes_atual = parcelas_mes.groupby("Método")["Valor"].sum().reset_index()
            st.bar_chart(data=resumo_metodo_mes_atual, x="Método", y="Valor")
        else:
            st.info("Nenhuma parcela para este mês.")

    with aba5:
        st.subheader("Simulador de Parcelas (não altera a base de dados)")

        with st.form("simulador"):
            valor_total_sim = st.number_input("Valor total da compra (R$)", min_value=0.0, format="%.2f", key="valor_sim")
            parcelas_sim = st.number_input("Quantidade de parcelas", min_value=1, step=1, key="parcelas_sim")
            enviar_sim = st.form_submit_button("Simular")

        if enviar_sim and valor_total_sim > 0 and parcelas_sim > 0:
            hoje = datetime.date.today()
            valor_parcela_base = round(valor_total_sim / parcelas_sim, 2)

            linhas_sim = []
            for i in range(parcelas_sim):
                mes = ((hoje.month + i) % 12) + 1
                ano = hoje.year + ((hoje.month + i) // 12)
                mes_ano = f"{mes:02d}/{ano}"

                if i < parcelas_sim - 1:
                    valor_parcela = valor_parcela_base
                else:
                    valor_parcela = round(valor_total_sim - valor_parcela_base * (parcelas_sim - 1), 2)

                linhas_sim.append({
                    "Parcela": i + 1,
                    "Valor": valor_parcela,
                    "Mes/Ano": mes_ano,
                    "Origem": "Simulação"
                })

            df_sim = pd.DataFrame(linhas_sim)

            st.write("### Distribuição das parcelas simuladas")
            st.table(df_sim)

            # Copia base real
            df_copy = df.copy()
            df_copy = df_copy[["Mes/Ano", "Valor"]].copy()
            df_copy["Origem"] = "Real"

            # Junta real + simulação
            df_comb = pd.concat([df_copy, df_sim], ignore_index=True)

            # Totais por mês e origem
            resumo_por_origem = df_comb.groupby(["Mes/Ano", "Origem"])["Valor"].sum().reset_index()
            resumo_total = df_comb.groupby("Mes/Ano")["Valor"].sum().reset_index()

            st.write("### Totais por mês (real vs simulação vs combinado)")
            tabela_final = resumo_total.merge(
                resumo_por_origem.pivot(index="Mes/Ano", columns="Origem", values="Valor").fillna(0),
                on="Mes/Ano",
                how="left"
            )
            st.table(tabela_final)

            st.write("### Impacto da simulação nos próximos meses")
            st.line_chart(data=resumo_total, x="Mes/Ano", y="Valor")

