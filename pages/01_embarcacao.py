import copy
import pandas as pd
import streamlit as st
from modules.validacao import verificar_hidro
from utils.estado import inicializar, aplicar
from utils.dados import ler, preparar_barco, registro_vazio, tabela_para_lista, COLUNAS_HIDRO, COLUNAS_GZ, COLUNAS_CASCO, json_bytes, csv_bytes

inicializar()
st.title("01 • Embarcação e importação AP1")
st.write("Não é necessário o código-fonte das APs. Aceita resultados em JSON, CSV ou XLSX, ou preenchimento manual. Nenhum dado hidrostático é gerado a partir de uma geometria fictícia.")
if st.session_state.prova_em_andamento: st.error("Ensaio ativo: finalize ou reinicie a prova antes de alterar a embarcação."); st.stop()
with st.expander("Importar dados — barco, hidrostática, GZ ou contorno",expanded=True):
    tipo=st.selectbox("Tipo de dado",["barco","hidro","gz","casco"],format_func=lambda x:{"barco":"Parâmetros da embarcação","hidro":"Tabela hidrostática","gz":"Curva GZ","casco":"Contorno do casco em planta (X,Y)"}[x])
    uploaded=st.file_uploader("Selecione CSV, XLSX ou JSON",type=["csv","xlsx","json"],key="upload_embarcacao")
    if uploaded and st.button("Validar e importar",type="primary"):
        try:
            dados=ler(uploaded,tipo)
            novo=copy.deepcopy(st.session_state.barco)
            if tipo=="barco": novo=preparar_barco(dados,novo)
            else:
                col={"hidro":COLUNAS_HIDRO,"gz":COLUNAS_GZ,"casco":COLUNAS_CASCO}[tipo]
                key={"hidro":"hidro_tabela","gz":"gz_curva","casco":"casco_contorno"}[tipo]
                novo[key]=tabela_para_lista(dados,col)
            verificar_hidro(sorted(novo["hidro_tabela"], key=lambda r:r["deslocamento_kg"]))
            aplicar(novo_barco=novo,descricao="Importação "+tipo)
            st.success("Dados importados e verificados; valores reais não foram completados automaticamente.")
        except Exception as e: st.error(str(e))
with st.form("barco_manual"):
    b=st.session_state.barco
    st.subheader("Parâmetros manuais")
    nome=st.text_input("Identificação",value=b.get("nome") or "")
    desc={"massa_base_kg":"Massa base — exclui cargas cadastradas (kg)","base_x_m":"LCG da massa base (m)","base_y_m":"TCG da massa base (m)","base_z_m":"KG da massa base (m)",
          "L_m":"Comprimento (m)","B_m":"Boca (m)","D_m":"Pontal (m)","z_min_m":"Limite mínimo físico de Z (m; opcional)","z_max_m":"Limite máximo físico de Z (m; opcional)","deslocamento_referencia_kg":"Deslocamento de referência (kg)",
          "calado_m":"Calado de referência (m)","km_m":"KM transversal de referência (m)","kb_m":"KB de referência (m)",
          "lcb_m":"LCB de referência (m)","lcf_m":"LCF de referência (m)","mtc_kgm_por_m":"MCT — momento por 1 m de trim (kg·m/m)",
          "fsm_kgm":"Momento de superfície livre efetivo (kg·m; 0 se comprovadamente ausente)",
          "gz_deslocamento_kg":"Deslocamento correspondente à curva GZ (kg)","gz_kg_referencia_m":"KG da curva GZ importada (m)"}
    inputs={}
    c1,c2=st.columns(2)
    for idx,(key,label) in enumerate(desc.items()):
        with (c1 if idx%2==0 else c2):
            inputs[key]=st.text_input(label,value="" if b.get(key) is None else str(b[key]),key="inp_"+key,help="Deixe em branco se não houver dado. Não informe zero para indicar ausência.")
    if st.form_submit_button("Salvar dados manuais"):
        try:
            novo=preparar_barco({"nome":nome,**inputs},b)
            for k in ("massa_base_kg","L_m","B_m","D_m","deslocamento_referencia_kg"):
                if novo.get(k) is not None and novo[k]<(0 if k=="massa_base_kg" else 1e-300):raise ValueError(f"{k} deve ser não negativo para massa base, positivo nos demais")
            if novo.get("fsm_kgm") is not None and novo["fsm_kgm"]<0:raise ValueError("FSM não pode ser negativo")
            aplicar(novo_barco=novo,descricao="Atualização manual dos dados")
            st.success("Parâmetros salvos")
        except ValueError as e:st.error(str(e))

st.divider()
st.subheader("Tabelas AP1 e entrada manual")
for tipo,col,chave in [("Hidrostática",COLUNAS_HIDRO,"hidro_tabela"),("Curva GZ",COLUNAS_GZ,"gz_curva"),("Casco planta",COLUNAS_CASCO,"casco_contorno")]:
    with st.expander(tipo):
        linhas=st.session_state.barco[chave]
        df=pd.DataFrame(linhas,columns=col)
        editado=st.data_editor(df,num_rows="dynamic",key="edit_"+chave,use_container_width=True)
        if st.button("Salvar tabela "+tipo,key="btn_"+chave):
            try:
                novo=copy.deepcopy(st.session_state.barco)
                novo[chave]=tabela_para_lista(editado.to_dict("records"),col)
                if chave=="hidro_tabela":
                    novo[chave]=sorted(novo[chave],key=lambda r:r["deslocamento_kg"])
                    verificar_hidro(novo[chave])
                elif chave=="gz_curva":
                    if any(r["angulo_graus"] is None or r["gz_m"] is None for r in novo[chave]):raise ValueError("Preencha ângulo e GZ")
                    novo[chave]=sorted(novo[chave],key=lambda r:r["angulo_graus"])
                elif chave=="casco_contorno":
                    if any(r["x_m"] is None or r["y_m"] is None for r in novo[chave]):raise ValueError("Contorno exige X e Y")
                aplicar(novo_barco=novo,descricao="Salvar "+tipo)
                st.success("Tabela salva")
            except Exception as e:st.error(str(e))
        st.download_button("Exportar CSV "+tipo,csv_bytes(linhas),file_name=chave+".csv",key="download_"+chave)
st.download_button("Exportar dados do barco (JSON)",json_bytes(st.session_state.barco),file_name="embarcacao.json")
st.caption("Tabela hidrostática: deslocamento kg e calado/KM m, ordenados. Interpolação apenas dentro da faixa. A curva GZ só será adaptada para outro KG se deslocamento e superfície livre permitirem.")

st.divider()
st.subheader("Integrar uma condição global AP1.2 sem duplicar massas")
st.write("Se a AP1.2 fornece **deslocamento total** e CG global, e você já cadastrou as cargas individuais dessa condição, é possível recuperar a massa/CG remanescente (base) por balanço de momentos. A operação não altera o cadastro até sua confirmação.")
with st.form("recuperar_base_ap1"):
    a,b,c,d=st.columns(4)
    delta_ap=a.text_input("Δ total AP1.2 (kg)",key="ap_delta")
    x_ap=b.text_input("LCG total AP1.2 (m)",key="ap_lcg")
    y_ap=c.text_input("TCG total AP1.2 (m)",key="ap_tcg")
    z_ap=d.text_input("KG total AP1.2 (m)",key="ap_kg")
    if st.form_submit_button("Derivar massa base pelos dados AP1.2"):
        try:
            if not all([delta_ap,x_ap,y_ap,z_ap]):raise ValueError("Para a massa e todos os centros, informe Δ, LCG, TCG e KG totais")
            total=float(delta_ap)
            cargas=st.session_state.cargas
            somac=sum(c["massa_kg"] for c in cargas)
            mb=total-somac
            if mb<=0:raise ValueError("Massa base derivada deve ser positiva; confira se as cargas já foram incluídas no deslocamento")
            novo=copy.deepcopy(st.session_state.barco)
            novo["massa_base_kg"]=mb
            for axis,cv in [("x_m",float(x_ap)),("y_m",float(y_ap)),("z_m",float(z_ap))]:
                novo["base_"+axis]=(total*cv-sum(c["massa_kg"]*c[axis] for c in cargas))/mb
            novo["deslocamento_referencia_kg"]=total
            from modules.carregamento import calcular
            conf=calcular(novo,cargas)
            for k,v in [("lcg_m",float(x_ap)),("tcg_m",float(y_ap)),("kg_m",float(z_ap))]:
                if abs(conf[k]-v)>1e-9:raise ValueError("Erro de fechamento de momentos "+k)
            aplicar(novo_barco=novo,descricao="Derivar base da condição AP1.2")
            st.success(f"Massa base derivada: {mb:.6g} kg; centros recuperados por Σm·r/Δ. Confirme o referencial de coordenadas.")
        except Exception as ex:st.error(str(ex))
