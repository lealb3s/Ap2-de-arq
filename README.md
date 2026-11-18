# Simulador de Prova de Inclinação — Python + Streamlit

Aplicativo acadêmico **independente das AP1 anteriores**. Importa arquivos de resultados AP1.1 (hidrostática), AP1.2 (cargas) e AP1.3 (GZ) via CSV/XLSX/JSON ou entrada manual. A ausência dos códigos-fonte anteriores não impede a instalação.

## Instalação local

```bash
python -m venv .venv
# Windows: .venv\Scripts\activate
# Linux/macOS: source .venv/bin/activate
python -m pip install -r requirements.txt
streamlit run app.py
```

Testes (sem Streamlit): `python -m pytest -q`.

## GitHub e Streamlit Community Cloud

1. Envie **todo o conteúdo deste diretório** para a raiz do repositório GitHub (incluindo subpastas `pages`, `modules`, `components`, `utils`, `visualization`).
2. Configure o repositório como fonte do Streamlit Community Cloud.
3. Informe `app.py` como arquivo principal e uma versão de Python compatível com as dependências.
4. Aguarde a instalação a partir de `requirements.txt` e abra a aplicação.
5. As entradas da sessão são temporárias: exporte os dados na página 09 antes de encerrar. Não existe banco de dados persistente.

## Uso passo a passo

1. **01 — Embarcação:** insira deslocamento de referência, KM, massa base e CG da massa base, contorno de planta se existente, tabela hidrostática e curva GZ. Dados vazios permanecem desconhecidos. `fsm_kgm=0` só quando a inexistência de superfície livre é comprovada.
2. **02 — Carregamento:** cadastre/importa massas e seus CG (X,Y,Z). Cada massa cadastrada **não** pode aparecer novamente na massa base. Use o botão de posição sugerida apenas como geometria nominal (editável).
3. **03 — Interação:** arraste as cargas em planta (X/Y) e ajuste X/Y/Z/massa nos campos. O desenho sem contorno importado é um retângulo **nominal**, não geometria real. Há desfazer/refazer e restaurar.
4. **04 — Pesos:** informe 3 alternativas e limites reais de acesso/massa/altura/ângulo/precisão. Sem limites, não há recomendação válida.
5. **05 — Pêndulos:** configure no mínimo dois e compare outros três comprimentos.
6. **06 — Prova virtual:** congele a condição de carregamento. Mova somente Y, registre leituras positivas, negativas e retornos a zero. Forneça limite angular na página 07 antes de registrar. Para oscilações, ative modelo dinâmico somente com Ixx e c conhecidos. Sem eles, a leitura é **quase estática teórica**.
7. **07 — Erros:** defina os erros sistemáticos e aleatórios e vento como momento conhecido em N·m. Os efeitos valem para as próximas leituras.
8. **08 — Redução:** faça o gráfico tangente versus momento, regressão linear, GM, KG quando KM e FSM estiverem disponíveis, análise de resíduos e sensibilidade. Também recebe medições reais independentes da simulação.
9. **09 — Relatório:** exporte JSON, CSV, HTML e pacote ZIP de resultados.

### Campos aceitos nos arquivos

- **Barco JSON:** `nome`, `massa_base_kg`, `base_x_m`, `base_y_m`, `base_z_m`, `L_m`, `B_m`, `D_m`, `z_min_m`, `z_max_m`, `deslocamento_referencia_kg`, `calado_m`, `km_m`, `kb_m`, `lcb_m`, `lcf_m`, `fsm_kgm`, `mtc_kgm_por_m`, `gz_deslocamento_kg`, `gz_kg_referencia_m`, `hidro_tabela`, `gz_curva`, `casco_contorno`. O JSON completo exportado na página 01 é um modelo. CSV ou XLSX do barco pode usar colunas `campo,valor` ou uma única linha com os parâmetros.
- **Hidrostática CSV/XLSX:** colunas `deslocamento_kg,calado_m,km_m,kb_m,lcb_m,lcf_m,mtc_kgm_por_m`. Apenas três primeiras obrigatórias; deslocamento em ordem crescente. Se só um ponto, o cálculo é válido para **exatamente** aquele deslocamento.
- **Cargas CSV/XLSX:** `id,nome,categoria,massa_kg,x_m,y_m,z_m,comp_m,larg_m,alt_m`. Os quatro últimos podem ser opcionais (não X/Y/Z). O ID pode estar vazio.
- **Curva GZ CSV/XLSX:** `angulo_graus,gz_m`. Para modificar o KG da curva, informe também o deslocamento e o KG de referência no cadastro do barco.
- **Contorno do casco:** `x_m,y_m` em planta; não é geometria 3D de carena nem é usado para hidrostática.
- **Medições experimentais:** `momento_kgm,tangente,estavel,fonte` (o CSV de oito ou mais posições tem que ser validado pelo responsável).

## Estrutura

`app.py` entrada; `pages/` páginas nativas; `modules/` física, validação, processamento; `visualization/` gráficos; `components/cargo_drag/` componente JS de arraste; `utils/` estado e import/export; `tests/` testes automatizados; `data/` exemplos de esquemas **sem números operacionais**.

## Hipóteses e limites

**Leia `REFERENCIAS.md`.** Não há modelagem de pressão hidrostática em uma malha real, hidrostatica 3D, trim não linear, alagamento, vento calculado a partir de formas, capacidade do convés, nem procedimento validado de certificação. Não forneça valores artificialmente para contornar bloqueios. O desenho rotaciona uma secção retangular **esquemática**, enquanto o cálculo de pequeno ângulo usa GM e os dados da condição real.

## Limitações dos testes

Unit tests verificam conservação de massa, troca de cargas, hidrostática, equações metacêntricas, pêndulos, regressão e um exemplo publicado. Como o ambiente de desenvolvimento pode não ter Streamlit, execute a prova de navegação/arraste também localmente ou no Cloud antes de uso em aula. Os testes **não** validam uma embarcação específica nem a completude da prova de inclinação real.

**Importação AP1.2 por dados globais:** na página 01, após importar as cargas, informe Δ e os três centros totais AP1.2 para derivar automaticamente massa e centro da parte não cadastrada, mantendo fechamento de momentos. Não é necessário ter os arquivos `.py` anteriores.
