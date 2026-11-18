import copy
import pandas as pd
import streamlit as st
from modules.validacao import ordenar_hidro_tabela
from utils.estado import inicializar, aplicar
from utils.mapeamento import identificar_tipo_tabela
from utils.dados import ler, preparar_barco, registro_vazio, tabela_para_lista, COLUNAS_HIDRO, COLUNAS_GZ, COLUNAS_CASCO, json_bytes, csv_bytes
from utils.ui_importacao import controles_tabela, mapear_campos, aplicar_mapeamento
from utils.importacao import verificar_unidade_declarada,aliases_barco

inicializar()
st.title("01 • Embarcação e importação AP1")
st.write("Não é necessário o código-fonte das APs. Aceita resultados em JSON, CSV ou XLSX, ou preenchimento manual. Nenhum dado hidrostático é gerado a partir de uma geometria fictícia.")
if st.session_state.prova_em_andamento: st.error("Ensaio ativo: finalize ou reinicie a prova antes de alterar a embarcação."); st.stop()
with st.expander("Importar dados — barco, hidrostática, GZ ou contorno", expanded=True):
    st.caption("Envie primeiro o arquivo. Para CSV/XLSX, a categoria é sugerida pelos cabeçalhos; confira antes de importar.")
    uploaded=st.file_uploader("Selecione CSV, XLSX ou JSON", type=["csv","xlsx","json"], key="upload_embarcacao")
    if uploaded:
        try:
            aba,linha_cabecalho,decimal_virgula,sugerido=controles_tabela(uploaded,'embarcacao')
            eh_json=uploaded.name.lower().endswith('.json')
            preliminares=(ler(uploaded,'hidro',aba=aba,decimal_virgula=decimal_virgula,
                             cabecalho_linha=linha_cabecalho) if not eh_json else None)
            cabecalhos=list(dict.fromkeys(k for r in (preliminares or []) if isinstance(r,dict)
                                        for k in r if k!='__linha_origem__'))
            # Reclassifica se a linha de cabeçalho foi alterada manualmente.
            if preliminares is not None:sugerido=identificar_tipo_tabela(cabecalhos)
            tipos=['— Escolha o tipo de dado —','barco','hidro','gz','casco']
            nomes={'barco':'Parâmetros da embarcação','hidro':'Tabela hidrostática',
                   'gz':'Curva GZ','casco':'Contorno do casco em planta (X,Y)'}
            import hashlib
            uid=hashlib.sha1(uploaded.getvalue()).hexdigest()[:10]
            tipo=st.selectbox('Tipo de dado',tipos,
                              index=tipos.index(sugerido) if sugerido in tipos else 0,
                              format_func=lambda x:nomes.get(x,x),
                              key=f'tipo_embarcacao_{uid}_{aba}_{linha_cabecalho}')
            if sugerido in ('cargas','leituras'):
                pagina='02 • Carregamento' if sugerido=='cargas' else '08 • Processamento'
                st.info(f'A aba foi reconhecida como **{sugerido}**. Para importá-la, use **{pagina}** no menu lateral.')
            if sugerido in nomes:
                st.info(f'A aba parece conter **{nomes.get(sugerido,sugerido)}**. '
                        'Confirme os campos e as unidades antes de importar.')
            if tipo=='— Escolha o tipo de dado —':
                st.warning('Selecione explicitamente o tipo de dado. Uma aba auxiliar não deve ser importada como dados hidrostáticos.')
                st.stop()
            if tipo=="barco" and sugerido=="hidro":
                raise ValueError("Esta planilha contém várias condições hidrostáticas, não uma ficha de parâmetros do barco. "
                                 "Escolha 'Tabela hidrostática' em 'Tipo de dado'.")
            dados=(preliminares if tipo!="barco" and preliminares is not None
                   else ler(uploaded,tipo,aba=aba,decimal_virgula=decimal_virgula,cabecalho_linha=linha_cabecalho))
            if tipo!="barco":
                if not isinstance(dados,list) or not dados or not isinstance(dados[0],dict):
                    raise ValueError("A tabela selecionada está vazia ou não contém registros tabulares")
                col={"hidro":COLUNAS_HIDRO,"gz":COLUNAS_GZ,"casco":COLUNAS_CASCO}[tipo]
                obrig={"hidro":["deslocamento_kg","calado_m","km_m"],
                       "gz":COLUNAS_GZ,"casco":COLUNAS_CASCO}[tipo]
                with st.container(border=True):
                    st.markdown('**Associe os campos originais aos campos do simulador.**')
                    mapeamento=mapear_campos(dados,tipo,col,obrig,
                                  f'embarcacao_{uid}_{aba}_{linha_cabecalho}')
                    if tipo=='hidro':
                        st.info('Importe somente deslocamento, calado, KM transversal e grandezas opcionais. '
                                'Não use KM longitudinal como KM transversal; KG/GM vazios são aceitáveis.')
                    fator_m=1.0
                    fator_kg=1.0
                    fator_graus=1.0
                    if tipo=="hidro":
                        ua,ub=st.columns(2)
                        unidade_peso=ua.selectbox("Unidade do deslocamento NA TABELA *",["Selecione","kg","t (tonelada métrica)"],key=f"unid_delta_hidro_{uid}_{aba}_{linha_cabecalho}")
                        unidade_comp=ub.selectbox("Unidade de calado, KM, KB, LCB e LCF NA TABELA *",["Selecione","m","cm","mm"],key=f"unid_comp_hidro_{uid}_{aba}_{linha_cabecalho}")
                        fator_kg={"kg":1.0,"t (tonelada métrica)":1000.0}.get(unidade_peso)
                        fator_m={"m":1.0,"cm":0.01,"mm":0.001}.get(unidade_comp)
                        st.caption("MCT é importado sem conversão: deve estar em kg·m por metro de trim. Se tiver outra unidade, converta-o antes de importar.")
                    elif tipo=="gz":
                        ua,ub=st.columns(2)
                        unidade_ang=ua.selectbox("Unidade do ângulo NA TABELA *",["Selecione","graus","radianos"],key=f"unid_angulo_gz_{uid}_{aba}_{linha_cabecalho}")
                        unidade_comp=ub.selectbox("Unidade do GZ NA TABELA *",["Selecione","m","cm","mm"],key=f"unid_comp_gz_{uid}_{aba}_{linha_cabecalho}")
                        from math import degrees
                        fator_graus={"graus":1.0,"radianos":degrees(1.0)}.get(unidade_ang)
                        fator_m={"m":1.0,"cm":0.01,"mm":0.001}.get(unidade_comp)
                    else:
                        unidade_comp=st.selectbox("Unidade das coordenadas X e Y NA TABELA *",["Selecione","m","cm","mm"],key=f"unid_comp_casco_{uid}_{aba}_{linha_cabecalho}")
                        fator_m={"m":1.0,"cm":0.01,"mm":0.001}.get(unidade_comp)
                # Prévia dos dados de origem, sem modificar os números.
                st.dataframe(pd.DataFrame(dados).head(8),use_container_width=True)
            if tipo=='barco':
                st.dataframe(pd.DataFrame([{'Parâmetro':k,'Valor recebido':v} for k,v in dados.items()]),
                             use_container_width=True,hide_index=True)
                st.caption('LPP não é convertido automaticamente em L_m. A identificação do referencial é necessária.')
                if preliminares is not None:
                    _dados_barco,_ignorados=aliases_barco(preliminares)
                    if _ignorados:
                        st.warning('Grandezas não associadas automaticamente: '+', '.join(_ignorados)+
                                   '. Preencha manualmente os parâmetros não reconhecidos, quando aplicável.')
                # Um Excel de dados principais pode omitir a unidade de B, D e Td.
                # Exigir que o usuário a confirme impede assumir SI sem evidência.
                _campos_metrico={'L_m','B_m','D_m','calado_m','km_m','kb_m','lcb_m','lcf_m',
                                 'base_x_m','base_y_m','base_z_m','gz_kg_referencia_m',
                                 'z_min_m','z_max_m'}
                _campos_massa={'massa_base_kg','deslocamento_referencia_kg','gz_deslocamento_kg'}
                _tem_comp=any(k in dados and dados[k] is not None and str(dados[k]).strip()
                              for k in _campos_metrico)
                _tem_massa=any(k in dados and dados[k] is not None and str(dados[k]).strip()
                              for k in _campos_massa)
                if eh_json:
                    st.info('JSON do simulador: pressupõe campos canônicos em SI, conforme documentação.')
                    unidade_barco_comp='m';unidade_barco_massa='kg'
                else:
                    unidade_barco_comp=(st.selectbox('Unidade das dimensões da ficha *',
                                          ['Selecione','m','cm','mm'],
                                          key=f'unid_ficha_comp_{uid}_{aba}') if _tem_comp else 'm')
                    unidade_barco_massa=(st.selectbox('Unidade das massas da ficha *',
                                          ['Selecione','kg','t (tonelada métrica)'],
                                          key=f'unid_ficha_massa_{uid}_{aba}') if _tem_massa else 'kg')
            if st.button("Validar e importar",type="primary",key=f"btn_import_{uid}_{aba}_{tipo}"):
                if tipo=="barco":
                    if not dados:
                        raise ValueError('Não há parâmetros reconhecidos. Confira a aba e os nomes dos campos.')
                    from utils.dados import numero_localizado
                    if unidade_barco_comp=='Selecione' or unidade_barco_massa=='Selecione':
                        raise ValueError('Confirme a unidade das dimensões e massas desta ficha.')
                    for key, val in list(dados.items()):
                        if key=='nome' or isinstance(val,(list,dict)) or val is None or not str(val).strip():
                            continue
                        numeric=numero_localizado(val,key,decimal_virgula)
                        if key in _campos_metrico:
                            numeric *= {'m':1.0,'cm':0.01,'mm':0.001}[unidade_barco_comp]
                        elif key in _campos_massa:
                            numeric *= {'kg':1.0,'t (tonelada métrica)':1000.0}[unidade_barco_massa]
                        dados[key]=numeric
                    novo=preparar_barco(dados,copy.deepcopy(st.session_state.barco))
                    # Uma tabela importada previamente permanece intacta, mas deve ser válida.
                    novo["hidro_tabela"]=ordenar_hidro_tabela(novo.get("hidro_tabela",[]))
                else:
                    faltantes=[campo for campo in obrig if mapeamento[campo]=="— Não importar —"]
                    if faltantes:
                        raise ValueError("Associe as colunas obrigatórias: "+", ".join(faltantes)+". Se não existirem, importe uma tabela adequada.")
                    ativos=[c for c in mapeamento.values() if c!="— Não importar —"]
                    if len(ativos)!=len(set(ativos)):
                        raise ValueError("Uma coluna do arquivo foi associada a mais de um campo. Corrija o mapeamento.")
                    if fator_m is None or fator_kg is None or fator_graus is None:
                        raise ValueError("Confirme explicitamente as unidades dos valores no arquivo antes de importar.")
                    # Evita tratar tonelada como quilograma ou milímetro como metro
                    # quando a unidade está expressa literalmente no cabeçalho.
                    if tipo=='hidro':
                        for field in ('deslocamento_kg',):
                            header=mapeamento.get(field)
                            if header!='— Não importar —':
                                verificar_unidade_declarada(header,'t' if unidade_peso.startswith('t ') else unidade_peso,field)
                        for field in ('calado_m','km_m','kb_m','lcb_m','lcf_m'):
                            header=mapeamento.get(field)
                            if header!='— Não importar —':
                                verificar_unidade_declarada(header,unidade_comp,field)
                    elif tipo=='gz':
                        for field,selected in (('angulo_graus',unidade_ang),('gz_m',unidade_comp)):
                            header=mapeamento.get(field)
                            if header!='— Não importar —':
                                verificar_unidade_declarada(header,selected,field)
                    else:
                        for field in ('x_m','y_m'):
                            header=mapeamento.get(field)
                            if header!='— Não importar —':
                                verificar_unidade_declarada(header,unidade_comp,field)
                    linhas=aplicar_mapeamento(dados,mapeamento,obrig)
                    registros=tabela_para_lista(linhas,col,decimal_virgula=decimal_virgula)
                    if not registros:
                        raise ValueError("A importação está vazia; confira a aba e as linhas da tabela.")
                    if tipo=="hidro":
                        for r in registros:
                            if r["deslocamento_kg"] is not None: r["deslocamento_kg"]*=fator_kg
                            for campo in ("calado_m","km_m","kb_m","lcb_m","lcf_m"):
                                if r[campo] is not None: r[campo]*=fator_m
                        registros=ordenar_hidro_tabela(registros)
                        chave="hidro_tabela"
                    elif tipo=="gz":
                        for i,r in enumerate(registros,1):
                            if r["angulo_graus"] is None or r["gz_m"] is None:
                                raise ValueError(f"Curva GZ: linha {r.get('__linha_origem__',i)}, preencha ângulo e GZ")
                            r["angulo_graus"]*=fator_graus
                            r["gz_m"]*=fator_m
                        registros.sort(key=lambda r:r["angulo_graus"])
                        chave="gz_curva"
                    else:
                        for i,r in enumerate(registros,1):
                            if r["x_m"] is None or r["y_m"] is None:
                                raise ValueError(f"Contorno: linha {r.get('__linha_origem__',i)}, informe X e Y")
                            r["x_m"]*=fator_m
                            r["y_m"]*=fator_m
                        chave="casco_contorno"
                    # Preserva a origem da linha apenas para diagnóstico; não grava como grandeza física.
                    for r in registros:r.pop('__linha_origem__',None)
                    novo=copy.deepcopy(st.session_state.barco)
                    novo[chave]=registros
                aplicar(novo_barco=novo,descricao="Importação "+tipo)
                st.success("Dados importados, associados e validados. Nenhum parâmetro faltante foi inventado.")
        except Exception as e:
            st.error("Não foi possível importar: "+str(e))
            st.info("Confira o tipo de tabela, a aba do Excel, os cabeçalhos e as unidades; se necessário, envie o arquivo para conferir o mapeamento.")
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
                    novo[chave] = ordenar_hidro_tabela(novo[chave])
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
