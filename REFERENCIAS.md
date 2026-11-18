# Fundamentação científica, fontes e hipóteses

**Escopo:** planejamento didático, simulação quasiestática, dinâmica linear com parâmetros informados e análise de uma prova de inclinação. **Não** é um instrumento de certificação. A Administração competente deve aprovar os procedimentos do ensaio real. Valores numéricos de deslocamento, geometria, GM, KM, centros, resistência do convés, comprimento dos pêndulos e momentos de vento **não são definidos pelo software**.

## Fontes verificadas

1. **IMO — International Code on Intact Stability, 2008 (2008 IS Code), Resolução MSC.267(85)**, capítulo 8 (inclining test), especialmente 8.2.2 e 8.4, e Anexo 1. Texto oficial: <https://wwwcdn.imo.org/localresources/en/KnowledgeCentre/IndexofIMOResolutions/MSCResolutions/MSC.267%2885%29.pdf>. Reprodução navegável do capítulo 8: <https://www.imorules.com/GUID-CEDF12C8-5469-4BB1-B9EA-F2B2EE264DB6.html> e <https://www.imorules.com/GUID-22FA8614-F52E-4FE7-8519-8FECB4F626E9.html>. Identifica dois pêndulos como mínimo recomendado, três preferíveis, faixa de cerca de 1 a 4 graus de cada lado para inclinação, e sequência padrão de oito movimentos, sujeita às exceções e à Administração. O app **não presume** cumprimento regulatório.
2. **US Coast Guard, Marine Safety Center — Plan Review Guideline GEN-02, *Submission of Stability Test Results*** (28 maio 2020): <https://www.dco.uscg.mil/Portals/9/MSC/PRG/PRG.GEN-02.2020.05.28.Submission%20of%20Stability%20Test%20Results.pdf>. Exige documentação de momento-tangente, condições da prova e superfície livre; usar na avaliação documental, não como substituto da autoridade local.
3. **OpenNAOE — Hydrostatics and Stability, cap. 10, *The Inclining Experiment***: <https://opennaoe.org/books/hydrostatics-stability/ch10/>. Equações (10.1), (10.2), (10.3), (10.4), (10.7); exemplos 10.1 e 10.2 usados na validação independente.
4. **Rawson & Tupper, Basic Ship Theory** e **Lewis (ed.), Principles of Naval Architecture**: bibliografia clássica de consulta para fundamentos de estabilidade; sem citação de números de páginas não consultados. Não foram extraídos coeficientes nem tabelas desses livros.

## Convenções

- X (m): longitudinal, aumentando no sentido da proa; origem escolhida na entrada; Y (m): transversal, **positivo para boreste**; Z (m): vertical, positivo acima da linha base.
- Δ (kg): **massa deslocada**, e não força. Se força (N) for necessária, usa-se g₀=9,80665 m/s², gravidade padrão. Momento de massa: kg·m; momento de força: N·m.
- Os dados de hidrostática devem ser da **mesma densidade, condição de trim e deslocamento** considerados no ensaio; o simulador não corrige densidade, trim acentuado ou deformação de casco automaticamente.

## Equações implementadas

| Cálculo | Equação | Entradas (SI) | Hipóteses, validade e limitações | Fonte |
|---|---|---|---|---|
| Condição de massa | Δ = m₀ + Σmᵢ | massa base e cargas (kg) | Massa base exclui cargas explicitadas; não contar massa duas vezes | Princípio de conservação de massa; PNA, estabilidade |
| Centros de gravidade | xG=Σ(mᵢxᵢ)/Δ; idem yG e zG incluindo massa base | kg, m | Corpos tratados por seus CG conhecidos; cargas que se deslocam exigem atualização | Mecânica estática; Rawson & Tupper |
| Momento inclinação de pesos | M = Σ mᵢ(yᵢ−yᵢ,0) | kg·m | Mesmos pesos e posições Z, X fixas durante a prova | OpenNAOE 10.1 |
| GM metacêntrico aparente | tan θ = M/(Δ GMef); θ=atan[M/(Δ GMef)] | M kg·m, Δ kg, GMef m, θ rad/graus | Somente ângulos pequenos, KM aproximadamente fixo; sem condições de grande banda | OpenNAOE eq. 10.1; IMO Anexo 1 |
| Pêndulo estático | x=L tanθ; θ=atan(x/L) | x e L (m), θ (°) | Pêndulo em equilíbrio; não descreve oscilação própria | OpenNAOE eq. 10.3 |
| Correção de superfície livre | FSC = FSM/Δ (m); GMef = KM − KG − FSC | FSM *efetivo* kg·m; Δ kg | FSM dado/calculado para densidades dos líquidos; constante em pequenos ângulos; variações por encosto do líquido não modeladas | OpenNAOE §10.5.1, eq. 10.7 |
| Regressão experimental | tanθᵢ = a + b Mᵢ; GMobs = 1/(Δb) | b (kg·m)⁻¹, Δ kg | Regressão linear com intercepto; exige momentos distintos, sinal coerente e Δ constante | OpenNAOE §10.4; USCG GEN-02 |
| KG da condição ensaiada | KGsol = KM − GMobs − FSM/Δ | m | Apenas quando KM e FSM foram informados e se referem à mesma condição | OpenNAOE eq. 10.7 |
| GZ ajustado a KG | GZ₂(θ)=GZ₁(θ)+(KG₁−KG₂)sinθ | m, rad | **Mesmo deslocamento, mesmo casco, TCG=0, FSM=0**; não se gera curva GZ de uma malha por esta identidade | Geometria de braço adriçante; PNA/Rawson & Tupper |
| Estimativa de trim | Mtrim = Δ(LCG−LCB); t = Mtrim/MCT | Δ kg, braços m, MCT kg·m/m, trim m | Linearizado e apenas com MCT fornecido; sem cálculo por hidrostática completa em trim | Princípio do momento longitudinal |
| Resolução angular pêndulo | δθ≈atan(r/L) | resolução linear r (m), comprimento L (m) | Estimativa geométrica; não é erro total nem incerteza de calibração | Geometria da leitura |
| Propagação de incerteza | σGM/GM ≈ √[(σm/m)²+(σd/d)²+(σL/L)²+(σΔ/Δ)²+(σx/x)²] | σ em unidades das respectivas variáveis | Pequenas incertezas independentes, leitura isolada; sem covariâncias nem correlações | Propagação diferencial de primeira ordem aplicada à eq. 10.1 |
| Dinâmica transitória OPCIONAL | Iφ̈+cφ̇+ΔgGMefφ=gM | I kg·m²; c N·m·s/rad; φ rad; M kg·m | Linearizada para pequenos ângulos; apenas se I e c forem fornecidos pelo usuário; não representa integralmente a hidrodinâmica de balanço | Equação de rolamento linear e balanço de momentos, física clássica |
| Interpolação hidrostática | H(Δ)=H₁+(H₂−H₁)(Δ−Δ₁)/(Δ₂−Δ₁) | Δ kg; H com unidade da coluna | Interpolação **interna e linear** na tabela AP1/hidrostática; NÃO extrapola; valores interpolados são aproximações dependentes da amostragem e do trim | Interpolação numérica linear, aplicada a dados de hidrostática |

## Limitações técnicas relevantes

1. **Sem hidrostática real:** L, B e D isolados não bastam para calcular KM/KB, deslocamento versus calado, GZ ou estabilidade em grandes ângulos. O app rejeita o cálculo que dependa deles.
2. **Deslocamento de base e cargas:** ao informar `massa_base_kg`, subtraia todas as massas que serão cadastradas como cargas. `deslocamento_referencia_kg` não substitui esse balanço: é o ponto da condição hidrostática.
3. **GZ e ângulos elevados:** o app exibe uma curva importada e permite correção limitada de KG; não integra carena imersa pela geometria tridimensional. A seção inclinada é ilustrativa e não prova equilíbrio hidrostático.
4. **Superfícies livres:** no ensaio, o GM observado é aparente; KG sólido requer a correção. Sem FSM conhecido, não se divulga KG sólido. Tanques com limites móveis da superfície precisam de modelagem adicional.
5. **Condição leve:** o KG obtido é da condição ensaiada; a passagem para lightship exige levantamento de pesos adicionados, retirados ou transferidos, com seus centros e correção do calado/hidrostática, ainda não incluída.
6. **Registros reais:** para prova real, pêndulos precisam de leituras e calibração. O fluxo de simulação etiqueta as medições como virtuais.
7. **Prova completa:** a IMO estabelece sequência padrão de oito movimentos de peso, com possibilidades de omitir conferência final de zero conforme condições citadas. O aplicativo exige no diagnóstico pelo menos oito registros, mas **não verifica** todos os requisitos documentais nem todas as posições prescritas.
8. **Critérios de aprovação:** resistência, segurança, limites de operação e tolerâncias são declarados pelo responsável; a sugestão multicritério é uma heurística acadêmica, não regulatória.

## Exemplo independente da literatura usado em teste

OpenNAOE, Ex. 10.1: Δ=2917,8 t; massas=5,00 t com deslocamentos 12,02 e 11,98 m; L=5,500 m; deflexão=0,182 m; KM=8,024 m; GM≈1,243 m; KG virtual≈6,781 m antes de correção da superfície livre. A comparação automatizada usa essas grandezas com tolerância de arredondamento. Esses números **NÃO** são importados automaticamente para uma embarcação do usuário.
