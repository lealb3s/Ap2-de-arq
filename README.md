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


## Importação de tabelas com cabeçalhos das AP1
Na página **01 • Embarcação**, envie o arquivo e, se for XLSX, escolha a aba.
O simulador sugere o **Tipo de dado** com base nos cabeçalhos (sem inferir unidades). Confirme que o tipo é
**Tabela hidrostática** antes de importar uma tabela de deslocamentos/calado/KM.
Associe as colunas reais do documento às colunas canônicas, por exemplo,
`Deslocamento (t)` → `deslocamento_kg`, `Calado` → `calado_m` e
`KMt` → `km_m`. Indique explicitamente se o deslocamento está em kg ou
toneladas métricas e as unidades das coordenadas. A conversão é aplicada
após validação. **Não presuma** que os números estejam em SI a partir do
título ou da ordem das colunas.

Para CSV brasileiro com números decimais usando vírgula, marque a opção
correspondente. Nas planilhas com várias abas, selecione a que efetivamente
contém a tabela. As linhas incompletas são rejeitadas com identificação
da linha/campo, enquanto linhas totalmente vazias são ignoradas.

O arquivo original não é substituído. A importação não substitui o
procedimento de conferir unidade, referencial de coordenadas, origem
da curva e correspondência do deslocamento.

## Importação específica: Hydrostatic Table (planilha enviada)

A aba **Hydrostatic Table** contém `T moldado [m]`, `Delta (deslocamento) [t]`,
`KM_t [m]`, `KB = VCB [m]`, `LCB [m]` e `LCF [m]`.
O importador sugere as correspondências exatas, que precisam ser confirmadas.
Selecione **Tabela hidrostática**, aba **Hydrostatic Table**, unidade de massa
**t (tonelada métrica)**, unidade de comprimento **m**, depois **Validar e importar**.
A coluna **KM_l [m]** é longitudinal e não deve ser confundida com **KM_t [m]**.
Os campos `KG (informado) [m]` e `GM_t [m]` do arquivo estão vazios; não
são preenchidos automaticamente. MCT e FSM não são deduzidos dessa tabela.
O arquivo original permanece intacto. Alternativamente, é possível importar o
CSV normalizado entregue separadamente (`hidrostatica_pronta_para_importar.csv`)
selecionando unidades **kg** e **m**.


## Correção do erro "CSV/XLSX de barco: colunas 'campo,valor' ou uma linha com parâmetros"

O arquivo `tabela hidrostática.xlsx` possui a aba **Planilha1** com 9 linhas hidrostáticas,
não uma ficha de dados gerais do barco. Nas versões anteriores, o seletor começava em
**Parâmetros da embarcação**, e o importador `barco` rejeitava tabelas com várias linhas.
Nesta versão, após escolher o arquivo, o app reconhece `T moldado [m]`,
`Delta (deslocamento) [t]` e `KM_t [m]` e **sugere Tabela hidrostática**. Confirme
as associações e selecione explicitamente **t (tonelada métrica)** e **m** antes de validar.
O formato original, os valores de deslocamento e os campos KG/GM vazios são preservados;
nenhum KM longitudinal (`KM_l`) substitui `KM_t`. Não tente importar esse arquivo
como **Parâmetros da embarcação**, pois esse esquema exige uma linha de dados ou pares `campo,valor`.

## Revisão do importador (versão 3 — múltiplas abas)

Esta versão adiciona `utils/importacao.py` e `utils/ui_importacao.py`.
Ao enviar um XLSX nas páginas 01, 02 ou 08, o aplicativo apresenta um **diagnóstico de todas as abas**,
mostrando quais têm um esquema reconhecível, qual a linha de cabeçalho provável e quais
parecem conter dados auxiliares não compatíveis. Uma aba desconhecida não vira hidrostática
por padrão. Para tabelas com capa, escolha a linha do cabeçalho manualmente.

**Exemplo real validado:** `hydrostatic_table (1)(1).xlsx`

| Aba | Interpretação segura | Destino |
| --- | --- | --- |
| Hydrostatic Table | Deslocamento, calado, KM transversal, KB, LCB e LCF | Página 01 → Tabela hidrostática |
| Dados principais | Ficha Grandeza/Valor (`nome`, `B`, `D`, `Td`) | Página 01 → Parâmetros da embarcação |
| Tabela de trabalho | Cotas de balizas e linhas d'água; **não são** dados de KM/GZ | Não importada como hidrostática |
| Origem das celulas | Rastreabilidade das cotas | Não importada como dado físico |
| Historico | Registro de operações da planilha | Não importado como dado físico |

A planilha `tabela hidrostática.xlsx` contém uma aba `Planilha1` com as nove condições;
a aba é identificada como hidrostática, não como cadastro de barco.

Para importar a primeira aba do exemplo acima, confirme **t** para deslocamento e **m** para as
cotas. Campos `KG` e `GM` em branco permanecem em branco; **KM_l** não substitui **KM_t**.
Para importar a aba `Dados principais`, confirme a unidade das dimensões antes de salvar.
`LPP` (comprimento entre perpendiculares) não é associado automaticamente ao campo genérico
`L_m`, pois os referenciais de comprimento devem ser verificados. `B`, `D` e `Td` são
associados por rótulos documentados e precisam da confirmação de unidade na interface.

Na página 02 há mapeamento próprio para **cargas** (nomes, massa e CG), com confirmação de
unidades. Na página 08 há mapeamento para **medições** (momento inclinante e tangente).
As três telas aceitam vírgula decimal **quando selecionada**, arquivos CSV com delimitadores
vírgula, ponto e vírgula ou tabulação, e UTF-8/Windows-1252. A importação rejeita colunas
duplicadas ou obrigatórias ausentes e informa o local da inconsistência sempre que possível.

**Não é importação universal de todas as grandezas do Excel.** Abas de malha de offsets,
relatórios livres e fórmulas sem esquema reconhecido são listadas, mas não convertidas
automaticamente para valores hidrostáticos ou geometria 3D. O programa não calcula hidrostática
a partir dessas cotas; essa seria uma funcionalidade de integração geométrica separada.

Testes: `python -m pytest -q`. Os testes de regressão baseados nos arquivos originais do usuário
são executados quando estes arquivos existem em `/mnt/data`, e ignorados quando ausentes;
os testes sintéticos do importador e os testes da Física Naval acompanham o pacote.
Não foi possível abrir a interface Streamlit nesta sessão de desenvolvimento; a navegação
visual e a atualização pelo Streamlit Community Cloud ainda precisam de conferência.
