# Quality Pipeline for Segmentation Datasets

## Objetivo

Desenvolver uma pipeline de **auditoria, validação e melhoria da qualidade de datasets de segmentação** exportados do CVAT.

O sistema terá como objetivo identificar automaticamente problemas que possam comprometer a qualidade das anotações e da composição do dataset, gerar métricas de qualidade, produzir relatórios e disponibilizar mecanismos de correção assistida ou automática.

A ferramenta busca reduzir erros de anotação, padronizar processos de Quality Assurance (QA), diminuir retrabalho e aumentar a confiabilidade dos datasets utilizados em projetos de Visão Computacional.

\---

# Problema

Em projetos de Visão Computacional, a qualidade dos dados utilizados no treinamento é um fator importante para a confiabilidade dos resultados.

Datasets de segmentação podem apresentar problemas como:

* imagens sem anotação;
* labels vazias;
* classes desbalanceadas;
* polígonos inválidos;
* máscaras muito pequenas ou muito grandes;
* imagens duplicadas;
* anotações duplicadas;
* classes cadastradas sem instâncias;
* inconsistências na distribuição das anotações;
* estruturas de dataset incompletas ou inválidas.

Em datasets grandes, identificar esses problemas manualmente pode consumir muito tempo e estar sujeito a falhas humanas.

Este projeto propõe uma pipeline automatizada para **Quality Assurance (QA)** de datasets de segmentação, capaz de analisar os dados, identificar problemas, gerar indicadores e relatórios e, posteriormente, auxiliar na correção dos casos encontrados.

\---

# Objetivo Geral

Desenvolver uma ferramenta capaz de analisar automaticamente datasets de segmentação, identificar problemas de qualidade, gerar métricas e relatórios e auxiliar no processo de revisão e melhoria dos dados antes de sua utilização no treinamento de modelos de Visão Computacional.

\---

# Objetivos Específicos

* validar a estrutura dos datasets;
* calcular estatísticas dos dados;
* identificar problemas de completude;
* validar anotações geométricas;
* analisar a distribuição das classes;
* detectar possíveis duplicidades;
* identificar outliers nas máscaras e anotações;
* calcular métricas de qualidade;
* gerar relatórios automatizados;
* disponibilizar uma interface visual para análise dos resultados;
* implementar mecanismos de correção assistida ou automática;
* permitir comparação entre diferentes versões de datasets;
* investigar experimentalmente a relação entre qualidade do dataset e desempenho dos modelos treinados.

\---

# Hipótese / Motivação

Uma pipeline automatizada de auditoria pode tornar o processo de validação de datasets mais **padronizado, reprodutível e escalável**, facilitando a identificação de problemas antes que os dados sejam utilizados no treinamento.

Além da identificação dos problemas, o projeto permitirá investigar experimentalmente se melhorias mensuráveis na qualidade dos datasets estão associadas a alterações no desempenho dos modelos treinados.

\---

# Visão Geral

O projeto será desenvolvido de forma incremental ao longo do período de estágio, com entregas parciais até a versão completa da solução.

A primeira grande entrega será um **MVP funcional focado em auditoria e análise de qualidade**. A partir dele, novas funcionalidades serão adicionadas progressivamente.

Fluxo geral:

```text
CVAT Export
     ↓
Dataset Parser
     ↓
Dataset Model
     ↓
Audit Engine
     ↓
Audit Results
     ↓
Quality Metrics
     ↓
Quality Report
     ↓
Dashboard
     ↓
Correction Engine
     ↓
Smart Audit
     ↓
Experimental Analysis
```

\---

# Arquitetura

## 1\. Dataset Parser

### Objetivo

Ler datasets exportados do CVAT e convertê-los para estruturas internas padronizadas.

### Formatos previstos

### YOLO Segmentation

```text
dataset/
├── images/
├── labels/
└── data.yaml
```

### COCO

```text
dataset/
├── images/
└── annotations.json
```

### Responsabilidades

* carregar datasets;
* validar a estrutura de diretórios;
* validar arquivos obrigatórios;
* indexar imagens;
* indexar anotações;
* associar imagens e anotações;
* normalizar informações para um formato interno comum.

\---

# 2\. Dataset Model

Depois do parsing, os dados serão representados em estruturas padronizadas para que os diferentes componentes da pipeline não dependam diretamente do formato de origem.

Estruturas conceituais:

```python
Dataset
Image
Annotation
Class
Polygon
Mask
BoundingBox
```

Exemplo:

```text
Dataset
 ├── images
 ├── classes
 └── annotations
```

Cada imagem poderá possuir:

```text
Image
 ├── width
 ├── height
 ├── path
 └── annotations
```

E cada anotação:

```text
Annotation
 ├── class\_id
 ├── polygon
 ├── mask
 └── bounding\_box
```

Essa camada permitirá que diferentes formatos de entrada sejam analisados pela mesma engine.

\---

# 3\. Audit Engine

## Objetivo

Executar verificações independentes sobre o dataset.

A arquitetura deverá permitir adicionar novos auditores sem alterar o funcionamento dos demais.

Estrutura proposta:

```text
auditors/
├── dataset\_statistics.py
├── missing\_annotations.py
├── class\_balance.py
├── polygon\_validator.py
├── small\_masks.py
├── large\_masks.py
├── duplicate\_images.py
└── duplicate\_annotations.py
```

Cada auditor deverá seguir uma interface comum e gerar resultados estruturados.

Exemplo conceitual:

```python
AuditResult(
    severity="warning",
    category="small\_mask",
    message="83 máscaras abaixo do limite definido"
)
```

\---

# 4\. Auditorias

## 4.1 Dataset Statistics

Calcular:

* número total de imagens;
* número total de classes;
* número total de instâncias;
* instâncias por classe;
* instâncias por imagem;
* distribuição das anotações.

\---

## 4.2 Missing Annotations

Detectar:

* imagens sem anotação;
* labels inexistentes;
* labels vazias;
* imagens sem instâncias;
* classes cadastradas sem instâncias.

Exemplo:

```text
Images: 5200

Images without annotations: 12
Empty labels: 7
Classes without instances: 1
```

\---

## 4.3 Class Distribution

Analisar a distribuição das classes.

Exemplo:

```text
Tomato    72%
Potato    21%
Radish     7%
```

O sistema deverá identificar classes potencialmente sub-representadas ou excessivamente dominantes de acordo com critérios configuráveis.

\---

## 4.4 Polygon Validation

Validar a geometria das anotações.

Detectar:

* polígonos inválidos;
* self-intersections;
* polígonos degenerados;
* coordenadas fora dos limites da imagem;
* número insuficiente de vértices;
* estruturas geométricas inconsistentes.

Exemplo:

```text
Invalid polygons: 7
Out-of-bounds polygons: 3
Degenerate polygons: 2
```

\---

## 4.5 Small Masks

Identificar máscaras com áreas muito pequenas em relação à imagem ou aos critérios definidos.

Possíveis causas:

* erro de anotação;
* objeto parcialmente visível;
* anotação incompleta;
* ruído;
* segmentação excessivamente fragmentada.

O objetivo inicial é **sinalizar casos suspeitos para revisão**, sem assumir automaticamente que são erros.

\---

## 4.6 Large Masks

Identificar máscaras que ocupem uma porcentagem excessivamente grande da imagem.

Possíveis causas:

* seleção incorreta;
* inclusão de regiões de fundo;
* anotação excessivamente abrangente.

Os casos encontrados deverão ser sinalizados para revisão.

\---

## 4.7 Duplicate Images

Detectar possíveis imagens duplicadas.

Técnica inicial:

```text
Perceptual Hash (pHash)
```

Técnicas complementares poderão ser utilizadas para casos de maior similaridade, incluindo:

```text
Image Embeddings
Similarity Search
```

O sistema deverá diferenciar, quando possível, entre:

```text
Duplicata exata
```

e

```text
Possível duplicata / imagem muito semelhante
```

\---

## 4.8 Duplicate Annotations

Detectar anotações potencialmente duplicadas.

Uma estratégia inicial poderá utilizar sobreposição geométrica:

```text
IoU
```

Exemplo conceitual:

```text
IoU > 0.90
```

pode ser utilizado como critério inicial para sinalizar possíveis duplicidades.

O limiar deverá ser configurável e validado experimentalmente.

\---

## 4.9 Annotation Consistency

Comparar características das anotações dentro de uma mesma classe para identificar possíveis outliers.

Exemplo:

```text
Tomato médio:
3000 px²

Tomato atual:
50 px²
```

O caso pode ser sinalizado como possível inconsistência para revisão.

\---

# 5\. Métricas de Qualidade

A pipeline deverá produzir métricas que representem diferentes dimensões do dataset.

## Dataset Coverage

Mede a proporção de imagens que possuem anotações válidas.

```text
Dataset Coverage =
Imagens anotadas / Imagens totais
```

\---

## Annotation Density

Mede a quantidade média de instâncias por imagem.

```text
Annotation Density =
Total de instâncias / Total de imagens
```

\---

## Class Distribution

Representa a proporção de instâncias pertencentes a cada classe.

Exemplo:

```text
Tomato     41.2%
Potato     32.8%
Radish     18.4%
Pear        7.6%
```

\---

## Class Balance

Indicador destinado a representar o grau de equilíbrio da distribuição das classes.

A métrica e sua fórmula serão definidas, documentadas e validadas durante a implementação.

\---

## Mask Coverage

Percentual da imagem ocupado por uma máscara.

Pode ser utilizado para identificar:

* máscaras muito pequenas;
* máscaras muito grandes;
* possíveis outliers.

\---

## Mask Area Distribution

Analisa a distribuição das áreas das máscaras e permite identificar:

* outliers;
* valores extremos;
* possíveis inconsistências;
* padrões incomuns.

\---

## Polygon Complexity

Mede características geométricas das anotações, como quantidade de vértices.

Pode ajudar a identificar:

* polígonos excessivamente complexos;
* polígonos excessivamente simplificados;
* outliers geométricos.

\---

## Duplicate Rate

Mede a proporção de imagens potencialmente duplicadas.

```text
Duplicate Rate =
Imagens duplicadas / Imagens totais
```

\---

# 6\. Quality Report

## Objetivo

Gerar um relatório consolidado dos resultados da auditoria.

### Formatos

```text
JSON
Markdown
HTML
CSV
```

### Exemplo

```text
DATASET QUALITY REPORT
────────────────────────────────

Images:             5200
Annotations:       18432
Classes:               8

Missing annotations:   12
Invalid polygons:       7
Duplicate images:       4
Small masks:            83

Class Distribution
────────────────────────────────

Tomato     41.2%
Potato     32.8%
Radish     18.4%
Pear        7.6%

Warnings:
- 12 imagens sem anotação
- 7 polígonos inválidos
- 4 imagens potencialmente duplicadas
- classe radish sub-representada

Recommendations:
- revisar imagens sem anotação
- revisar polígonos inválidos
- analisar imagens potencialmente duplicadas
- revisar distribuição da classe radish
```

\---

# 7\. Dashboard

## Objetivo

Disponibilizar uma interface visual para exploração dos resultados da auditoria.

### Tecnologias

* Streamlit
* Plotly
* Pandas

### Recursos

* estatísticas gerais;
* distribuição de classes;
* quantidade de problemas por categoria;
* filtros por classe;
* visualização de métricas;
* identificação de exemplos problemáticos;
* comparação entre auditorias;
* histórico de análises;
* comparação entre versões de datasets.

\---

# 8\. Correction Engine

## Objetivo

Auxiliar na correção dos problemas identificados pela pipeline.

A correção poderá ocorrer de duas formas:

```text
Correção assistida
        ↓
Revisão humana
        ↓
Aplicação da alteração
```

ou, em casos de baixo risco e regras bem definidas:

```text
Problema detectado
        ↓
Regra validada
        ↓
Correção automática
        ↓
Validação
```

### Exemplos

```text
15 imagens duplicadas detectadas

Deseja mover para revisão?

\[Sim] \[Não]
```

Ou:

```text
Classe possivelmente incorreta:

apple → pear

Confirma alteração?

\[Sim] \[Não]
```

As correções deverão manter rastreabilidade das alterações realizadas.

\---

# 9\. Smart Audit

## Objetivo

Expandir a capacidade de auditoria utilizando técnicas de Visão Computacional e Inteligência Artificial.

Possibilidades:

* integração com modelos de detecção;
* identificação de objetos potencialmente não anotados;
* detecção de anomalias;
* comparação semântica entre imagens;
* embeddings;
* busca por similaridade;
* sugestão de inconsistências;
* sugestão de possíveis correções.

\---

# 10\. Avaliação Experimental

Uma etapa importante do projeto será avaliar a pipeline em datasets reais.

Fluxo experimental:

```text
Dataset Original
       ↓
Auditoria
       ↓
Problemas Identificados
       ↓
Revisão / Correção
       ↓
Dataset Revisado
       ↓
Treinamento
       ↓
Avaliação do Modelo
       ↓
Comparação
```

A análise poderá investigar se melhorias mensuráveis na qualidade do dataset estão associadas a alterações no desempenho dos modelos treinados.

Dependendo da tarefa e do modelo utilizado, poderão ser analisadas métricas como:

```text
mAP
IoU
Precision
Recall
```

A relação entre qualidade dos dados e desempenho do modelo será tratada como uma questão experimental, permitindo comparar versões do dataset sob condições controladas.

\---

# 11\. MVP

A primeira grande entrega do projeto será um **MVP funcional da pipeline de auditoria**.

O MVP terá como foco principal:

```text
Dataset
   ↓
Parser
   ↓
Auditors
   ↓
Metrics
   ↓
Quality Report
```

### Escopo inicial

* suporte inicial a YOLO Segmentation;
* Dataset Parser;
* Dataset Statistics;
* Missing Annotations Auditor;
* Class Distribution Auditor;
* Polygon Validator;
* Small Masks Auditor;
* Large Masks Auditor;
* Duplicate Images Auditor;
* estrutura padronizada de `AuditResult`;
* métricas básicas;
* geração de relatório;
* testes automatizados.

### Exemplo de execução

```bash
python audit.py ./dataset
```

### Exemplo de saída

```text
Dataset Quality Report
────────────────────────────────

Images:             5200
Annotations:       18432
Classes:               8

Missing annotations:   12
Invalid polygons:        7
Duplicate images:        4
Small masks:            83

Class Distribution
────────────────────────────────

tomato       41.2%
potato       32.8%
radish       18.4%
pear          7.6%

Warnings:
- 12 imagens sem anotação
- 7 polígonos inválidos
- 4 imagens potencialmente duplicadas
- 83 máscaras pequenas
```

\---

# 12\. Critérios de Sucesso do MVP

O MVP será considerado concluído quando for capaz de:

* carregar um dataset de segmentação em formato suportado;
* validar sua estrutura básica;
* indexar imagens e anotações;
* executar múltiplos auditores;
* gerar resultados estruturados;
* identificar problemas de qualidade;
* calcular métricas básicas;
* gerar um relatório;
* possuir testes automatizados para os principais componentes.

\---

# 13\. Roadmap

O projeto será desenvolvido ao longo do período de estágio, com entregas parciais e incrementais até a conclusão da solução completa.

## Etapa 1 — Fundamentos e Arquitetura

* \[ ] estrutura inicial do projeto;
* \[ ] definição da arquitetura;
* \[ ] modelagem dos dados;
* \[ ] estudo da estrutura dos exports do CVAT;
* \[ ] suporte inicial ao formato YOLO Segmentation;
* \[ ] definição das interfaces dos auditores;
* \[ ] configuração dos testes.

\---

## Etapa 2 — MVP

* \[ ] Dataset Parser;
* \[ ] Dataset Statistics;
* \[ ] Missing Annotations Auditor;
* \[ ] Class Distribution Auditor;
* \[ ] Polygon Validator;
* \[ ] Small Masks Auditor;
* \[ ] Large Masks Auditor;
* \[ ] Duplicate Images Auditor;
* \[ ] estrutura padronizada de `AuditResult`;
* \[ ] métricas iniciais;
* \[ ] geração de relatório;
* \[ ] testes automatizados.

\---

## Etapa 3 — Expansão da Auditoria

* \[ ] suporte a COCO;
* \[ ] Duplicate Annotations;
* \[ ] Annotation Consistency;
* \[ ] métricas avançadas;
* \[ ] Mask Area Distribution;
* \[ ] Mask Coverage;
* \[ ] Polygon Complexity;
* \[ ] tratamento de diferentes níveis de severidade.

\---

## Etapa 4 — Dashboard

* \[ ] Streamlit Dashboard;
* \[ ] gráficos interativos;
* \[ ] filtros por classe;
* \[ ] visualização dos problemas;
* \[ ] histórico de auditorias;
* \[ ] comparação entre datasets;
* \[ ] comparação entre versões do mesmo dataset.

\---

## Etapa 5 — Correction Engine

* \[ ] identificação de correções de baixo risco;
* \[ ] correção assistida;
* \[ ] remoção ou isolamento de duplicatas;
* \[ ] remapeamento de classes;
* \[ ] validação após correção;
* \[ ] histórico das alterações;
* \[ ] possibilidade de rollback.

\---

## Etapa 6 — Smart Audit

* \[ ] integração com modelos de detecção;
* \[ ] identificação de objetos potencialmente não anotados;
* \[ ] detecção de anomalias;
* \[ ] embeddings;
* \[ ] similaridade semântica;
* \[ ] sugestões de inconsistências;
* \[ ] sugestões de correção.

\---

## Etapa 7 — Avaliação Experimental

* \[ ] seleção de datasets para avaliação;
* \[ ] definição dos experimentos;
* \[ ] comparação entre versões dos datasets;
* \[ ] treinamento de modelos;
* \[ ] avaliação antes e depois das melhorias;
* \[ ] análise das métricas;
* \[ ] documentação dos resultados;
* \[ ] consolidação das conclusões.

\---

# 14\. Estrutura Inicial do Projeto

```text
quality-pipeline/
│
├── README.md
├── requirements.txt
├── pyproject.toml
├── .gitignore
│
├── src/
│   └── quality\_pipeline/
│       │
│       ├── parsers/
│       │   ├── yolo.py
│       │   └── coco.py
│       │
│       ├── models/
│       │   ├── dataset.py
│       │   ├── image.py
│       │   └── annotation.py
│       │
│       ├── auditors/
│       │   ├── statistics.py
│       │   ├── missing\_annotations.py
│       │   ├── class\_balance.py
│       │   ├── polygon\_validator.py
│       │   ├── small\_masks.py
│       │   ├── large\_masks.py
│       │   ├── duplicate\_images.py
│       │   └── duplicate\_annotations.py
│       │
│       ├── metrics/
│       │   ├── completeness.py
│       │   ├── class\_balance.py
│       │   ├── mask\_coverage.py
│       │   └── duplicate\_rate.py
│       │
│       ├── reports/
│       │   ├── json\_report.py
│       │   ├── markdown\_report.py
│       │   └── html\_report.py
│       │
│       ├── correction/
│       │   └── ...
│       │
│       └── cli.py
│
├── tests/
│   ├── test\_parsers/
│   ├── test\_auditors/
│   ├── test\_metrics/
│   └── test\_reports/
│
├── dashboard/
│   └── app.py
│
├── notebooks/
│
└── docs/
```

\---

# 15\. Tecnologias

## Backend

* Python
* Pandas
* NumPy

## Computer Vision e Geometria

* OpenCV
* Shapely
* scikit-image

## Dataset Formats

* YOLO Segmentation
* COCO

## Dashboard

* Streamlit
* Plotly

## Testing

* pytest

\---

# 16\. Resultados Esperados

Ao final do projeto, espera-se obter:

* uma pipeline reutilizável de auditoria de datasets;
* validação automatizada de datasets de segmentação;
* métricas quantitativas de qualidade;
* relatórios padronizados;
* dashboard para análise dos resultados;
* mecanismos de correção assistida e automática;
* capacidade de comparar versões de datasets;
* funcionalidades de auditoria inteligente;
* base experimental para investigar a relação entre qualidade dos dados e desempenho de modelos;
* redução do esforço manual necessário para processos de QA.

\---

# 17\. Visão de Longo Prazo

A visão do projeto é transformar a ferramenta em uma solução interna de **Quality Assurance para datasets de Visão Computacional**, capaz de:

```text
Validar
   ↓
Auditar
   ↓
Medir
   ↓
Reportar
   ↓
Comparar
   ↓
Corrigir
   ↓
Monitorar
   ↓
Investigar
```

O foco inicial será em datasets de segmentação exportados do CVAT, com arquitetura preparada para evolução para outros formatos, tarefas e métodos de auditoria.

\---
