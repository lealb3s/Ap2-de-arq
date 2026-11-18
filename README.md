# Simulador de prova de inclinação

Aplicação Streamlit em português para preparar uma condição de carregamento, executar uma prova virtual, processar leituras e exportar os resultados.

## Executar

Com Python 3.12, abra um terminal na pasta que contém `app.py` e execute:

```sh
python -m pip install -r requirements.txt
python -m streamlit run app.py
```

No Streamlit Community Cloud, envie o conteúdo desta pasta ao repositório, incluindo `.streamlit/config.toml`, e selecione `app.py` como arquivo principal.

## Usar com dados próprios

1. Em **Embarcação**, importe ou digite a massa base (sem as cargas que serão cadastradas), seus centros e o momento de superfície livre. Informe a tabela hidrostática ou o deslocamento de referência e KM transversal para uma condição única.
2. Em **Carregamento**, salve ao menos um peso com massa e coordenadas X, Y e Z. O eixo Y é positivo a boreste e Z é medido acima da linha base. Em **Movimentação**, confira a distribuição. Para o ensaio virtual, a condição inicial precisa ter TCG zero e GM efetivo positivo.
3. Em **Planejamento de pesos**, você pode comparar alternativas. Em **Pêndulos**, salve pelo menos dois comprimentos. Em **Condições do ensaio**, informe o limite angular e salve.
4. No **Ensaio virtual**, inicie a prova, mova o peso em Y e registre cada leitura. Ao encerrar, siga para **Processamento**. A regressão exige ao menos três momentos distintos com leituras de equilíbrio.
5. Em **Relatório**, baixe os resultados em HTML, JSON ou ZIP. Os dados ficam na sessão aberta do navegador. Salve os formulários antes de mudar de etapa.

Se já tiver medições, abra **Processamento** diretamente na tela inicial. Importe ou edite os valores de momento e tangente. Confira quais leituras estão estabilizadas e informe o deslocamento para calcular GM. Para obter KG sólido, informe também KM e o momento de superfície livre da mesma condição.

## Importação

Os modelos da pasta `data` mostram os campos aceitos. CSV aceita UTF-8 ou Windows-1252. No Excel (.xlsx), escolha uma aba por importação. É possível ajustar o cabeçalho, conferir as associações e confirmar as unidades antes de salvar. Tabelas auxiliares podem ficar de fora. Fichas de embarcação aceitam pares Grandeza/Valor ou uma única linha com os campos nas colunas. O JSON do simulador usa kg e m.

| Tabela | Campos essenciais |
| --- | --- |
| Hidrostática | Deslocamento, calado e KM transversal |
| Curva GZ | Ângulo e braço GZ |
| Contorno em planta | X e Y |
| Cargas | Nome, massa e coordenadas X, Y e Z |
| Medições | Momento em kg·m e tangente. O campo estavel identifica as leituras usadas na regressão. |

O deslocamento deve estar dentro da faixa de interpolação. Uma referência hidrostática isolada só vale para o deslocamento correspondente. Consulte `REFERENCIAS.md` para as hipóteses dos modelos e as fontes técnicas.
