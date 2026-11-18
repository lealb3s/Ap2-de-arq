import html
import io
import json
import zipfile
from datetime import datetime,timezone
import pandas as pd
import streamlit as st
from utils.estado import inicializar
from utils.dados import json_bytes,csv_bytes,normalizar

inicializar();st.title("09 • Relatório e exportação")
st.write("O relatório diferencia dados fornecidos, dados ausentes, cálculos e leituras virtuais. Não atribui conformidade regulamentar ao ensaio.")
s=st.session_state
pacote={k:normalizar(s[k]) for k in ("barco","cargas","leituras","movimentos","pendulos","configuracoes","erros","log_alteracoes")}
pacote["ultima_regressao"]=normalizar(s.get("ultima_regressao"))
pacote["param_regressao"]=normalizar(s.get("param_regressao"))
st.download_button("Baixar todos os dados (JSON)",json_bytes(pacote),file_name="dados_prova_inclinacao.json",mime="application/json")

# Relatório HTML autocontido; arquivos de origem em separado para auditabilidade.
def montar_html():
    b=s.barco; reg=s.get("ultima_regressao")
    nome=html.escape(str(b.get("nome") or "Não informado"))
    title="Relatório técnico — Prova de inclinação"
    resultado="Sem regressão calculada"
    if reg:
        kg="Não calculável: faltam KM e/ou FSM" if reg["kg_solido_m"] is None else f"{reg['kg_solido_m']:.6f} m"
        resultado=f"GM observado: {reg['gm_observado_m']:.6f} m; KG sólido: {kg}; R²: {reg['r2']:.6f}; n = {reg['n']}."
    def tab(rows):
        if not rows:return "<p>Sem registros.</p>"
        return pd.DataFrame(rows).to_html(index=False,escape=True,classes="tabela")
    return f'''<!doctype html><html lang="pt-BR"><meta charset="utf-8"><title>{title}</title>
<style>body{{font:15px/1.5 Arial,sans-serif;max-width:1000px;margin:40px auto;color:#1e293b}}h1,h2{{color:#0e7490}}table{{border-collapse:collapse;width:100%;font-size:12px}}td,th{{border:1px solid #cbd5e1;padding:7px;vertical-align:top}}th{{background:#e2e8f0}}.alerta{{border-left:4px solid #c2410c;padding:12px;background:#fff7ed}}</style>
<h1>{title}</h1><p>Embarcação: <b>{nome}</b></p><p>Gerado em UTC: {datetime.now(timezone.utc).isoformat()}</p>
<div class="alerta">Resultado acadêmico. A prova física, conferência de instrumentos e aprovação da autoridade competente não são substituídas por esta ferramenta. O formato HTML permite impressão em PDF pelo navegador.</div>
<h2>Dados de embarcação</h2>{tab([b])}
<h2>Cargas</h2>{tab(s.cargas)}
<h2>Instrumentos</h2>{tab(s.pendulos)}
<h2>Movimentos</h2>{tab(s.movimentos)}
<h2>Leituras</h2>{tab([{k:v for k,v in r.items() if k not in ('pendulos','posicoes_y')} for r in s.leituras])}
<h2>Regressão e resultados</h2><p>{resultado}</p>
<h2>Condições de validade</h2><p>Aproximação metacêntrica para pequenos ângulos. GM estimado por regressão tanθ vs momento inclinado. FSM fornecido para a condição ensaiada. Sem dados completos, os resultados são parciais.</p>
<h2>Limitações</h2><p>Não inclui determinação de hidrostática por malha 3D, certificação de instrumentos, forças reais de vento ou amarras, nem ângulos grandes sem GZ de mesma condição.</p>
<h2>Fontes técnicas</h2><p>IMO 2008 IS Code, resolução MSC.267(85), capítulo 8 e anexo 1; USCG MSC PRG GEN-02; Rawson & Tupper; Lewis; OpenNAOE, cap. 10. Consulte REFERENCIAS.md para links e hipóteses.</p>
</html>'''

report=montar_html()
st.download_button("Baixar relatório técnico em HTML",report.encode("utf-8"),file_name="relatorio_prova_inclinacao.html",mime="text/html")

def make_zip():
    buf=io.BytesIO()
    with zipfile.ZipFile(buf,"w",compression=zipfile.ZIP_DEFLATED) as z:
        z.writestr("dados_prova_inclinacao.json",json_bytes(pacote))
        z.writestr("cargas.csv",csv_bytes(s.cargas))
        z.writestr("movimentos.csv",csv_bytes(s.movimentos))
        z.writestr("leituras.csv",csv_bytes([{k:v for k,v in r.items() if k not in ("pendulos","posicoes_y")} for r in s.leituras]))
        z.writestr("relatorio.html",report.encode("utf-8"))
        if s.get("ultima_regressao"):
            z.writestr("regressao.json",json_bytes(s.ultima_regressao))
            import plotly.io as pio
            from visualization.graficos import ajuste,residuos
            z.writestr("grafico_regressao.html",pio.to_html(ajuste(s.ultima_regressao),full_html=True,include_plotlyjs="cdn"))
            z.writestr("grafico_residuos.html",pio.to_html(residuos(s.ultima_regressao),full_html=True,include_plotlyjs="cdn"))
    return buf.getvalue()

st.download_button("Baixar pacote completo de resultados (ZIP)",make_zip(),file_name="resultados_prova_inclinacao.zip",mime="application/zip",type="primary")
st.info("Gráficos HTML exportados usam Plotly via CDN e necessitam internet ao abrir. O relatório HTML é autocontido e pode ser impresso em PDF localmente.")
