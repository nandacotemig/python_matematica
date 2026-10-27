import streamlit as st
import pandas as pd
import plotly.express as px

st.set_page_config(page_title="Afazeres Domésticos", page_icon="🏠", layout="wide")

ANOS = [2016, 2017, 2018, 2019, 2022]
REGIOES = ["Brasil", "Norte", "Nordeste", "Sudeste", "Sul", "Centro-Oeste"]
FAIXAS = ["14 a 29 anos", "30 a 49 anos", "50 a 59 anos", "60 anos ou mais"]


@st.cache_data
def ler_tabela_raca(arquivo):
    planilha = pd.ExcelFile(arquivo)
    lista = []
    for ano in ANOS:
        df = pd.read_excel(planilha, sheet_name=str(ano), header=None)
        df = df.iloc[8:41, 0:8]
        df.columns = ["local", "total", "total_branca", "total_preta_parda",
                      "homem_branco", "homem_preto_pardo", "mulher_branca", "mulher_preta_parda"]
        df["ano"] = ano
        lista.append(df)
    dados = pd.concat(lista)
    dados["local"] = dados["local"].str.strip()
    dados["homens"] = (dados["homem_branco"] + dados["homem_preto_pardo"]) / 2
    dados["mulheres"] = (dados["mulher_branca"] + dados["mulher_preta_parda"]) / 2
    dados["diferenca"] = dados["mulheres"] - dados["homens"]
    return dados


@st.cache_data
def ler_tabela_idade(arquivo):
    planilha = pd.ExcelFile(arquivo)
    lista = []
    for ano in ANOS:
        df = pd.read_excel(planilha, sheet_name=str(ano), header=None)
        df = df.iloc[7:40]
        for i in range(len(FAIXAS)):
            coluna = 4 + i * 3
            parte = pd.DataFrame({
                "local": df[0].str.strip(),
                "faixa": FAIXAS[i],
                "homens": df[coluna + 1],
                "mulheres": df[coluna + 2],
                "ano": ano,
            })
            lista.append(parte)
    return pd.concat(lista)


st.sidebar.title("Filtros")

upload_111 = st.sidebar.file_uploader("Tabela 1.1.1 (todas as pessoas)", type=["xls"])
upload_112 = st.sidebar.file_uploader("Tabela 1.1.2 (ocupadas por idade)", type=["xls"])
upload_113 = st.sidebar.file_uploader("Tabela 1.1.3 (ocupadas por raça)", type=["xls"])

todos = ler_tabela_raca(upload_111 or "dados/tabela_1_1_1.xls")
idade = ler_tabela_idade(upload_112 or "dados/tabela_1_1_2.xls")
ocupados = ler_tabela_raca(upload_113 or "dados/tabela_1_1_3.xls")

lista_estados = sorted([x for x in todos["local"].unique() if x not in REGIOES])
estados = st.sidebar.multiselect("Estados", lista_estados, default=["Amazonas", "Bahia", "Ceará", "Pernambuco"])
ano = st.sidebar.selectbox("Ano", ANOS[::-1])
faixa = st.sidebar.selectbox("Faixa etária", ["Todas"] + FAIXAS)

if not estados:
    st.warning("Escolha pelo menos um estado na barra lateral.")
    st.stop()

dados_ano = todos[todos["ano"] == ano]
filtrado = dados_ano[dados_ano["local"].isin(estados)]
brasil = dados_ano[dados_ano["local"] == "Brasil"].iloc[0]

st.title("🏠 Afazeres Domésticos e Cuidado de Pessoas")
st.write(f"Horas semanais dedicadas aos afazeres domésticos e ao cuidado de pessoas (14 anos ou mais) - IBGE/PNAD Contínua {ano}")

col1, col2, col3, col4 = st.columns(4)
col1.metric("Homens (Brasil)", f"{brasil['homens']:.1f} h")
col2.metric("Mulheres (Brasil)", f"{brasil['mulheres']:.1f} h")
col3.metric("Diferença média (Brasil)", f"{brasil['diferenca']:.1f} h")
col4.metric("Diferença média (estados)", f"{filtrado['diferenca'].mean():.1f} h")

aba1, aba2, aba3, aba4, aba5 = st.tabs(["Sexo", "Sexo e raça", "Evolução", "Trabalho fora", "Notícias"])

with aba1:
    st.subheader("Horas semanais por sexo e estado")
    grafico = filtrado.melt(id_vars="local", value_vars=["homens", "mulheres"], var_name="Sexo", value_name="Horas")
    grafico["Sexo"] = grafico["Sexo"].replace({"homens": "Homens", "mulheres": "Mulheres"})
    fig = px.bar(grafico, x="local", y="Horas", color="Sexo", barmode="group", text_auto=".1f",
                 labels={"local": "Estado"}, color_discrete_map={"Homens": "#2b5c8f", "Mulheres": "#d95f02"})
    st.plotly_chart(fig, width="stretch")

    st.subheader("Quantas horas a mais as mulheres fazem")
    fig = px.bar(filtrado.sort_values("diferenca"), x="diferenca", y="local", orientation="h", text_auto=".1f",
                 labels={"diferenca": "Horas a mais por semana", "local": "Estado"})
    fig.add_vline(x=brasil["diferenca"], line_dash="dash", line_color="red", annotation_text="Brasil")
    st.plotly_chart(fig, width="stretch")

with aba2:
    nomes = {
        "homem_branco": "Homem branco",
        "homem_preto_pardo": "Homem preto/pardo",
        "mulher_branca": "Mulher branca",
        "mulher_preta_parda": "Mulher preta/parda",
    }
    grafico = filtrado.melt(id_vars="local", value_vars=list(nomes), var_name="Grupo", value_name="Horas")
    grafico["Grupo"] = grafico["Grupo"].replace(nomes)

    st.subheader("Horas semanais por sexo e raça")
    fig = px.bar(grafico, x="local", y="Horas", color="Grupo", barmode="group", text_auto=".1f",
                 labels={"local": "Estado"})
    st.plotly_chart(fig, width="stretch")

    st.subheader("Distribuição das horas em todos os estados")
    todos_estados = dados_ano[~dados_ano["local"].isin(REGIOES)]
    box = todos_estados.melt(id_vars="local", value_vars=list(nomes), var_name="Grupo", value_name="Horas")
    box["Grupo"] = box["Grupo"].replace(nomes)
    fig = px.box(box, x="Grupo", y="Horas", color="Grupo", points="all", hover_name="local")
    st.plotly_chart(fig, width="stretch")

with aba3:
    st.subheader("Evolução da diferença entre mulheres e homens")
    evolucao = todos[todos["local"].isin(estados + ["Brasil"])]
    fig = px.line(evolucao, x="ano", y="diferenca", color="local", markers=True,
                  labels={"ano": "Ano", "diferenca": "Horas a mais (mulheres)", "local": "Local"})
    fig.update_xaxes(tickvals=ANOS)
    st.plotly_chart(fig, width="stretch")
    st.caption("Não houve pesquisa desse tema em 2020 e 2021 por causa da pandemia.")

with aba4:
    st.subheader("Todas as pessoas x pessoas que trabalham fora")
    ocupados_ano = ocupados[(ocupados["ano"] == ano) & (ocupados["local"].isin(estados))]
    comparacao = pd.DataFrame({
        "Estado": list(filtrado["local"]) * 2,
        "Grupo": ["Todas as pessoas"] * len(filtrado) + ["Trabalham fora"] * len(ocupados_ano),
        "Mulheres": list(filtrado["mulheres"]) + list(ocupados_ano["mulheres"]),
        "Homens": list(filtrado["homens"]) + list(ocupados_ano["homens"]),
    })
    escolha = st.radio("Mostrar", ["Mulheres", "Homens"], horizontal=True)
    fig = px.bar(comparacao, x="Estado", y=escolha, color="Grupo", barmode="group", text_auto=".1f",
                 labels={escolha: "Horas por semana"})
    st.plotly_chart(fig, width="stretch")

    st.subheader("Quem trabalha fora, por faixa etária")
    idade_ano = idade[(idade["ano"] == ano) & (idade["local"].isin(estados))]
    if faixa != "Todas":
        idade_ano = idade_ano[idade_ano["faixa"] == faixa]
    grafico = idade_ano.melt(id_vars=["local", "faixa"], value_vars=["homens", "mulheres"], var_name="Sexo", value_name="Horas")
    grafico["Sexo"] = grafico["Sexo"].replace({"homens": "Homens", "mulheres": "Mulheres"})
    fig = px.bar(grafico, x="faixa", y="Horas", color="Sexo", barmode="group", facet_col="local", text_auto=".1f",
                 labels={"faixa": "Faixa etária"}, color_discrete_map={"Homens": "#2b5c8f", "Mulheres": "#d95f02"})
    st.plotly_chart(fig, width="stretch")

with aba5:
    col1, col2 = st.columns(2)
    with col1:
        st.subheader("Carga Mental Feminina")
        st.image("imagens/carga_mental.jpg")
        st.write("Além das tarefas em si, as mulheres costumam ficar responsáveis por planejar e lembrar de tudo "
                 "que a casa e a família precisam. Esse trabalho invisível pesa na saúde mental.")
        st.markdown("- [Le Monde Diplomatique: Você poderia ter me pedido - o trabalho invisível das mulheres](https://diplomatique.org.br/voce-poderia-ter-me-pedido-o-trabalho-invisivel-das-mulheres/)")
        st.markdown("- [Folha de Pernambuco: Saúde mental e a sobrecarga feminina](https://www.folhape.com.br/noticias/opiniao/saude-mental-e-a-sobrecarga-feminina-quem-cuida-de-quem-cuida/320078/)")
        st.markdown("- [O Povo: Protagonizado por mulheres, trabalho de cuidado segue invisível](https://www.opovo.com.br/noticias/enem/2023/11/05/amp/protagonizado-por-mulheres-trabalho-de-cuidado-segue-invisivel-entenda.html)")
    with col2:
        st.subheader("Economia do Cuidado")
        st.image("imagens/economia_cuidado.jpg")
        st.write("Cuidar de crianças, idosos e da casa é um trabalho que movimenta a economia, mas não é pago "
                 "e quase sempre fica com as mulheres, principalmente as mulheres negras.")
        st.markdown("- [O Povo+: Economia do cuidado, um trabalho invisível e não remunerado](https://mais.opovo.com.br/reportagens-especiais/mulheres-e-cuidado-economia-sociedade/2024/06/25/economia-do-cuidado-um-trabalho-invisivel-e-nao-remunerado-das-mulheres.html)")
        st.markdown("- [Forbes: Mulheres são responsáveis por mais de 75% do trabalho não remunerado](https://forbes.com.br/forbes-mulher/2023/11/economia-do-cuidado-mulheres-sao-responsaveis-por-mais-de-75-do-trabalho-nao-remunerado/)")
        st.markdown("- [Politize: O que é economia do cuidado](https://www.politize.com.br/economia-do-cuidado/)")
    st.caption("Imagens: Wikimedia Commons.")
