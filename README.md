# Quality Pipeline for Segmentation Datasets

## 1. Visão Geral

O **Quality Pipeline for Segmentation Datasets** é um projeto voltado à auditoria, validação e melhoria da qualidade de datasets de segmentação utilizados em projetos de Visão Computacional.

A proposta é desenvolver uma ferramenta capaz de analisar datasets, identificar possíveis problemas nas imagens e anotações, calcular métricas de qualidade e gerar relatórios que auxiliem os processos de revisão e melhoria dos dados.

O sistema será desenvolvido para trabalhar com diferentes projetos e domínios, sem depender de categorias específicas, como frutas, vegetais ou outros tipos de objetos.

O primeiro formato de entrada será o **COCO Segmentation**, com suporte futuro ao **Ultralytics YOLO Segmentation**.

## 2. Problema

Em projetos de Visão Computacional, a qualidade dos dados utilizados no treinamento influencia diretamente a confiabilidade dos resultados dos modelos.

Datasets de segmentação podem apresentar problemas como:

- Imagens sem anotações.
- Registros de anotação incompletos ou inconsistentes.
- Classes desbalanceadas.
- Polígonos inválidos ou degenerados.
- Coordenadas fora dos limites das imagens.
- Máscaras muito pequenas ou muito grandes.
- Imagens duplicadas.
- Categorias cadastradas sem instâncias.
- Estruturas de dataset incompletas ou inválidas.
- Possíveis inconsistências entre anotações da mesma classe.

Em datasets grandes, identificar esses problemas manualmente pode consumir muito tempo e estar sujeito a falhas humanas.

O projeto propõe automatizar parte desse processo por meio de uma pipeline reutilizável de Quality Assurance (QA).

Os resultados das auditorias deverão auxiliar a identificação de problemas, sem classificar automaticamente toda anomalia como erro de anotação.

## 3. Objetivos

### Objetivo Geral

Desenvolver uma ferramenta capaz de analisar automaticamente datasets de segmentação, identificar problemas de qualidade, calcular métricas e gerar relatórios para auxiliar os processos de revisão e melhoria dos dados antes de sua utilização no treinamento de modelos de Visão Computacional.

### Objetivos Específicos

- Interpretar diferentes formatos de exportação de datasets.
- Padronizar internamente a representação dos dados.
- Validar estruturas de imagens e anotações.
- Identificar problemas de completude e consistência.
- Analisar a distribuição das categorias.
- Validar geometrias de segmentação.
- Identificar imagens potencialmente duplicadas.
- Analisar máscaras e anotações potencialmente anômalas.
- Calcular métricas de qualidade.
- Gerar relatórios automatizados.
- Disponibilizar uma interface visual para exploração dos resultados.
- Implementar mecanismos de correção assistida ou automática.
- Permitir comparação entre diferentes versões de datasets.
- Investigar experimentalmente a relação entre qualidade dos dados e desempenho dos modelos treinados.

## 4. Escopo e Formatos de Entrada

A arquitetura será independente do formato de origem dos dados.

### 4.1 COCO Segmentation

Será o formato prioritário da primeira versão funcional do projeto, pois é utilizado no fluxo de exportação e treinamento do ambiente de desenvolvimento.

O parser deverá interpretar as principais estruturas do arquivo `annotations.json`:

- `images`
- `categories`
- `annotations`

Também deverá suportar as diferentes representações de segmentação previstas pelo COCO:

- Polígonos.
- RLE (Run-Length Encoding).

As imagens serão localizadas utilizando os caminhos informados no JSON e um diretório raiz configurável.

### 4.2 Ultralytics YOLO Segmentation

Será o próximo formato a receber suporte.

O parser deverá interpretar:

- `data.yaml`;
- diretórios de imagens e anotações;
- arquivos TXT de segmentação;
- identificadores de classes;
- coordenadas de polígonos normalizadas;
- divisões do dataset, como train, val e test.

As coordenadas normalizadas deverão ser convertidas para pixels, utilizando as dimensões originais de cada imagem.

### 4.3 YOLO 1.1

O formato clássico YOLO 1.1 também foi analisado durante o desenvolvimento.

Esse formato representa anotações por bounding boxes e não será tratado como um formato de segmentação poligonal.

O suporte a formatos adicionais poderá ser avaliado futuramente conforme as necessidades dos projetos.

## 5. Arquitetura

A arquitetura do projeto será organizada em três responsabilidades principais:

**Parsers**

Responsáveis por interpretar os formatos externos e converter suas informações para os modelos internos.

**Models**

Responsáveis por representar os dados em estruturas padronizadas, independentes do formato de origem.

**Auditors**

Responsáveis por executar verificações de qualidade utilizando os modelos internos.

### Fluxo geral

```text
        COCO Dataset
              |
              v
          COCO Parser

        YOLO Dataset
              |
              v
          YOLO Parser
              |
              v
       Internal Dataset
              |
              v
         Audit Engine
              |
              v
         Audit Results
              |
              v
       Quality Metrics
              |
              v
       Quality Reports
              |
              v
          Dashboard
```

O objetivo é permitir que os mesmos auditores sejam utilizados independentemente do formato de entrada.

A documentação detalhada das decisões arquiteturais está disponível em `docs/architecture.md`.

## 6. Modelos Internos

Os modelos representam os principais elementos de um dataset de segmentação.

A implementação inicial utiliza classes Python baseadas em `dataclasses`.

### Category

Representa uma categoria existente no dataset.

Atributos:

- `id`: identificador da categoria dentro do dataset.
- `name`: nome da categoria.
- `supercategory`: agrupamento superior, quando disponível.

### Image

Representa uma imagem pertencente ao dataset.

Atributos:

- `id`: identificador interno da imagem.
- `file_name`: nome ou caminho relativo original da imagem.
- `width`: largura em pixels.
- `height`: altura em pixels.
- `resolved_path`: caminho local completo da imagem, quando disponível.

O caminho original é preservado separadamente do caminho local resolvido.

### Segmentation

Representa a geometria da segmentação independentemente do formato de origem.

São previstas duas representações:

**PolygonSegmentation**

Representa um ou mais polígonos compostos por pontos `(x, y)` em coordenadas de pixels.

**MaskSegmentation**

Representa uma máscara binária utilizando uma codificação RLE interna, independente das codificações específicas dos formatos externos.

### BoundingBox

Representa a caixa delimitadora de uma anotação.

Atributos:

- `x`: coordenada horizontal do canto superior esquerdo.
- `y`: coordenada vertical do canto superior esquerdo.
- `width`: largura da caixa.
- `height`: altura da caixa.

As coordenadas internas são expressas em pixels.

### Annotation

Representa uma instância de objeto anotada em uma imagem.

Atributos:

- `id`: identificador da anotação.
- `image_id`: referência à imagem relacionada.
- `category_id`: referência à categoria relacionada.
- `segmentation`: representação geométrica da segmentação, quando disponível.
- `bbox`: bounding box, quando disponível.
- `area`: área da anotação, quando disponível.
- `is_crowd`: indica se a anotação representa um agrupamento de objetos, quando essa informação existir.
- `attributes`: metadados adicionais associados à anotação.

### Dataset

Representa o conjunto completo de dados após a conversão para os modelos internos.

Atributos:

- `images`: lista de imagens.
- `categories`: lista de categorias.
- `annotations`: lista de anotações.
- `metadata`: informações gerais do dataset.

## 7. Padronização dos Dados

Os modelos internos não deverão depender diretamente das estruturas dos formatos COCO ou YOLO.

As principais regras de padronização são:

- Coordenadas geométricas expressas em pixels.
- Origem do sistema de coordenadas no canto superior esquerdo.
- Eixo X crescente da esquerda para a direita.
- Eixo Y crescente de cima para baixo.
- Categorias e identificadores preservados conforme os dados de origem.
- Caminhos de imagens resolvidos de forma configurável.
- Informações indisponíveis representadas como `None`, quando aplicável.
- Representações de segmentação convertidas para os modelos internos.

Os parsers serão responsáveis pelas conversões necessárias.

Os modelos representarão os dados, enquanto os auditors serão responsáveis pelas verificações de qualidade.

## 8. Audit Engine

O Audit Engine será responsável por executar diferentes auditorias sobre um dataset.

A arquitetura deverá permitir adicionar novos auditores sem modificar o funcionamento dos demais.

Cada auditor deverá seguir uma interface comum e produzir resultados estruturados.

A estrutura planejada de um resultado de auditoria deverá contemplar informações como:

```python
AuditResult(
    code="SMALL_MASK",
    severity="warning",
    message="Segmentação possivelmente pequena",
    image_id=10,
    annotation_id=25,
)
```

Os resultados poderão conter:

- Código do problema.
- Severidade.
- Mensagem descritiva.
- Identificador da imagem.
- Identificador da anotação, quando aplicável.
- Detalhes adicionais.

A interface e a estrutura de resultados serão definidas durante a implementação do Audit Engine.

## 9. Auditorias Planejadas

### 9.1 Dataset Statistics

Calcular informações gerais:

- Total de imagens.
- Total de categorias.
- Total de anotações.
- Quantidade de imagens por categoria.
- Quantidade de anotações por categoria.
- Média de anotações por imagem.
- Dimensões das imagens.

### 9.2 Missing Annotations

Identificar situações como:

- Imagens sem anotações.
- Referências para imagens inexistentes.
- Anotações associadas a imagens inexistentes.
- Categorias cadastradas sem instâncias.
- Registros incompletos ou inconsistentes.

A ausência de anotação não será considerada automaticamente um erro, pois alguns datasets podem conter imagens negativas legítimas.

### 9.3 Class Distribution

Analisar a distribuição das instâncias entre as categorias.

O objetivo será identificar categorias potencialmente sub-representadas ou excessivamente dominantes.

Os critérios e limiares serão configuráveis e deverão ser documentados.

### 9.4 Segmentation Validation

Analisar a estrutura e a geometria das segmentações.

Possíveis verificações:

- Polígonos malformados.
- Número insuficiente de vértices.
- Polígonos degenerados.
- Self-intersections.
- Coordenadas fora dos limites da imagem.
- Inconsistências na representação das máscaras.
- Áreas inválidas ou inconsistentes.

### 9.5 Small Masks

Identificar máscaras com áreas muito pequenas em relação à imagem ou aos critérios configurados.

Os casos encontrados deverão ser sinalizados para revisão.

### 9.6 Large Masks

Identificar máscaras que ocupem uma porcentagem potencialmente excessiva da imagem.

Os casos encontrados também deverão ser sinalizados para revisão.

### 9.7 Duplicate Images

Identificar imagens duplicadas ou potencialmente semelhantes.

A implementação poderá utilizar técnicas como:

- Hash exato.
- Perceptual Hash (pHash).
- Técnicas de similaridade visual.

É importante distinguir duplicatas exatas de imagens apenas semelhantes.

### 9.8 Annotation Consistency

Em uma etapa posterior, analisar características das anotações dentro de uma mesma categoria para identificar possíveis inconsistências.

Exemplos de características:

- Área.
- Dimensões da bounding box.
- Proporção entre largura e altura.
- Quantidade de vértices.
- Cobertura da imagem.

Os casos suspeitos deverão ser apresentados para revisão humana.

## 10. Métricas e Relatórios

A pipeline deverá calcular métricas que permitam compreender diferentes aspectos da qualidade do dataset.

Métricas previstas:

**Dataset Coverage**

Proporção de imagens com anotações, considerando as regras definidas para o dataset.

**Annotation Density**

Quantidade média de instâncias por imagem.

**Class Distribution**

Proporção de instâncias pertencentes a cada categoria.

**Mask Coverage**

Percentual da imagem ocupado pela máscara.

**Mask Area Distribution**

Distribuição das áreas das máscaras e identificação de possíveis outliers.

**Polygon Complexity**

Características geométricas das segmentações, incluindo quantidade de vértices.

Os critérios de avaliação e fórmulas deverão ser definidos e documentados durante a implementação.

A ferramenta não utilizará um indicador subjetivo único de qualidade do dataset. Os resultados serão apresentados por meio de métricas individuais e ocorrências identificadas pelas auditorias.

### Quality Reports

Os resultados das auditorias deverão ser consolidados em relatórios.

Formatos planejados:

- JSON.
- Markdown.
- HTML.
- CSV.

JSON e Markdown serão priorizados na primeira versão funcional.

## 11. MVP

A primeira grande entrega será um **MVP funcional de auditoria de datasets de segmentação**, utilizando COCO como formato inicial de entrada.

### Escopo do MVP

- Parser COCO.
- Modelos internos padronizados.
- Audit Engine.
- Estrutura comum de resultados (`AuditResult`).
- Dataset Statistics.
- Missing Annotations.
- Class Distribution.
- Segmentation Validation.
- Small Masks.
- Large Masks.
- Duplicate Images.
- Métricas básicas.
- Relatórios JSON e Markdown.
- Interface de linha de comando (CLI).
- Testes automatizados.

O escopo poderá ser ajustado conforme a complexidade das auditorias e a validação com o mentor.

### Fluxo esperado

```text
COCO Dataset
      |
      v
   COCO Parser
      |
      v
   Dataset Model
      |
      v
   Audit Engine
      |
      v
    Auditors
      |
      v
  Audit Results
      |
      v
 Quality Metrics
      |
      v
 Quality Report
```

### Critérios de sucesso do MVP

O MVP será considerado concluído quando for capaz de:

- Carregar um dataset COCO de segmentação.
- Interpretar imagens, categorias e anotações.
- Converter polígonos e RLE para as representações internas.
- Resolver caminhos de imagens de forma configurável.
- Construir um objeto `Dataset` consistente.
- Executar múltiplas auditorias.
- Identificar problemas e produzir resultados estruturados.
- Calcular métricas básicas.
- Gerar relatórios.
- Executar o fluxo por linha de comando.
- Possuir testes automatizados para os principais componentes.
- Ser validado com datasets reais e sintéticos.

## 12. Roadmap

O projeto será desenvolvido de forma incremental ao longo do período de estágio.

### Etapa 1 — Fundamentos e Arquitetura

- [x] Criação do repositório.
- [x] Configuração do ambiente Python.
- [x] Configuração do ambiente virtual.
- [x] Configuração do `pyproject.toml`.
- [x] Configuração do Pytest.
- [x] Estrutura inicial de diretórios.
- [x] Estudo dos exports do CVAT.
- [x] Análise do formato COCO.
- [x] Análise do formato Ultralytics YOLO Segmentation.
- [x] Definição da arquitetura dos modelos internos.
- [x] Implementação inicial de Category.
- [x] Implementação inicial de Image.
- [x] Implementação inicial de Segmentation.
- [x] Implementação inicial de BoundingBox.
- [x] Implementação inicial de Annotation.
- [x] Implementação inicial de Dataset.
- [x] Testes iniciais dos modelos.
- [x] Documentação inicial da arquitetura.

### Etapa 2 — Consolidação da Base

- [x] Padronização dos finais de linha com `.gitattributes`.
- [ ] Atualização e consolidação do README.
- [ ] Refinamento das validações estruturais dos modelos.
- [ ] Ampliação dos testes de casos extremos.
- [ ] Revisão final da arquitetura antes dos parsers.

### Etapa 3 — Parser COCO

- [ ] Implementação do COCO Parser.
- [ ] Leitura de `annotations.json`.
- [ ] Interpretação de imagens e categorias.
- [ ] Conversão de anotações.
- [ ] Suporte a polígonos.
- [ ] Suporte a RLE.
- [ ] Conversão de bounding boxes.
- [ ] Resolução configurável dos caminhos das imagens.
- [ ] Testes unitários e de integração.
- [ ] Validação com datasets reais.

### Etapa 4 — Audit Engine

- [ ] Definição da interface comum dos auditores.
- [ ] Implementação do modelo `AuditResult`.
- [ ] Organização e execução dos auditores.
- [ ] Tratamento de severidades.
- [ ] Testes automatizados.

### Etapa 5 — Auditorias e Métricas

- [ ] Dataset Statistics.
- [ ] Missing Annotations.
- [ ] Class Distribution.
- [ ] Segmentation Validation.
- [ ] Small Masks.
- [ ] Large Masks.
- [ ] Duplicate Images.
- [ ] Métricas iniciais.
- [ ] Validação dos critérios com datasets reais.

### Etapa 6 — Relatórios e CLI

- [ ] Geração de relatórios JSON.
- [ ] Geração de relatórios Markdown.
- [ ] Integração da pipeline completa.
- [ ] Interface de linha de comando.
- [ ] Testes de ponta a ponta.
- [ ] Validação dos critérios de sucesso do MVP.

### Etapa 7 — Suporte a YOLO

- [ ] Implementação do Ultralytics YOLO Segmentation Parser.
- [ ] Interpretação de `data.yaml`.
- [ ] Leitura das imagens e arquivos TXT.
- [ ] Conversão das coordenadas normalizadas.
- [ ] Conversão para os modelos internos.
- [ ] Execução dos mesmos auditores em COCO e YOLO.
- [ ] Testes de integração.

### Etapa 8 — Dashboard

- [ ] Desenvolvimento do Dashboard com Streamlit.
- [ ] Gráficos interativos.
- [ ] Filtros por categoria.
- [ ] Visualização dos resultados das auditorias.
- [ ] Histórico de análises.
- [ ] Comparação entre datasets.
- [ ] Visualização de exemplos problemáticos.

### Etapa 9 — Correction Engine

- [ ] Identificação de correções de baixo risco.
- [ ] Correção assistida.
- [ ] Aplicação controlada de correções automáticas.
- [ ] Validação após correção.
- [ ] Histórico das alterações.
- [ ] Possibilidade de rollback.

### Etapa 10 — Smart Audit

- [ ] Integração com modelos de detecção.
- [ ] Identificação de objetos potencialmente não anotados.
- [ ] Detecção de anomalias.
- [ ] Embeddings e similaridade visual.
- [ ] Sugestões de inconsistências.
- [ ] Sugestões de revisão e correção.

### Etapa 11 — Avaliação Experimental

- [ ] Seleção de datasets para avaliação.
- [ ] Definição dos experimentos.
- [ ] Comparação entre versões dos datasets.
- [ ] Treinamento de modelos.
- [ ] Avaliação antes e depois das melhorias.
- [ ] Análise das métricas.
- [ ] Documentação dos resultados e conclusões.

## 13. Estrutura Atual do Projeto

```text
Quality-Pipeline-for-Segmentation-Datasets/
│
├── .gitattributes
├── .gitignore
├── README.md
├── pyproject.toml
│
├── data/
│   ├── raw/
│   └── sample/
│
├── docs/
│   └── architecture.md
│
├── src/
│   └── quality_pipeline/
│       ├── __init__.py
│       │
│       ├── models/
│       │   ├── __init__.py
│       │   ├── category.py
│       │   ├── image.py
│       │   ├── segmentation.py
│       │   ├── bounding_box.py
│       │   ├── annotation.py
│       │   └── dataset.py
│       │
│       ├── parsers/
│       │   └── __init__.py
│       │
│       └── auditors/
│           └── __init__.py
│
└── tests/
    ├── test_package.py
    ├── test_models/
    │   ├── test_category.py
    │   ├── test_image.py
    │   ├── test_segmentation.py
    │   ├── test_bounding_box.py
    │   ├── test_annotation.py
    │   └── test_dataset.py
    │
    ├── test_parsers/
    └── test_auditors/
```

Os diretórios `data/raw/` e demais arquivos de datasets locais são ignorados pelo Git.

## 14. Tecnologias

### Implementadas

- Python.
- Setuptools.
- Pytest.
- Dataclasses.
- pathlib.
- JSON.

### Tecnologias a avaliar conforme a implementação

- NumPy.
- Pillow ou OpenCV.
- Shapely.
- Ferramentas de leitura e conversão de máscaras COCO/RLE.
- Streamlit.
- Plotly.

A inclusão de dependências será feita conforme a necessidade técnica de cada componente.

## 15. Resultados Esperados

Ao final do projeto, espera-se obter:

- Uma pipeline reutilizável de auditoria de datasets.
- Suporte a diferentes formatos de entrada.
- Validação automatizada de datasets de segmentação.
- Identificação de possíveis problemas de qualidade.
- Métricas quantitativas.
- Relatórios padronizados.
- Dashboard para exploração dos resultados.
- Mecanismos de correção assistida ou automática.
- Comparação entre versões de datasets.
- Auditoria inteligente.
- Base experimental para investigar a relação entre qualidade dos dados e desempenho dos modelos.

## 16. Visão de Longo Prazo

A visão do projeto é transformar a ferramenta em uma solução interna de **Quality Assurance para datasets de Visão Computacional**.

O fluxo de evolução será:

```text
Importar
   |
   v
Padronizar
   |
   v
Auditar
   |
   v
Medir
   |
   v
Reportar
   |
   v
Revisar
   |
   v
Corrigir
   |
   v
Comparar
   |
   v
Investigar
```

A arquitetura deverá permitir a evolução da ferramenta para diferentes projetos, formatos e tarefas de Visão Computacional, mantendo a separação entre interpretação dos dados, representação interna e auditoria.