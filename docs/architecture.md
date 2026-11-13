# Arquitetura do Projeto

**Projeto:** Quality Pipeline for Segmentation Datasets

**Status:** Arquitetura definida e modelos internos implementados inicialmente.

**Última atualização:** 13/11/2026

---

## 1. Objetivo

Este documento registra as decisões arquiteturais e os contratos técnicos que orientam a implementação do Quality Pipeline for Segmentation Datasets.

O projeto deverá suportar diferentes formatos de exportação de datasets de segmentação, inicialmente COCO e futuramente Ultralytics YOLO Segmentation.

Embora esses formatos representem informações semelhantes, possuem estruturas diferentes para armazenar imagens, categorias, anotações e segmentações.

Para evitar dependência de um formato específico, o projeto utilizará modelos internos padronizados.

Essa representação permitirá que os mecanismos de auditoria trabalhem independentemente do formato de origem dos dados.

## 2. Princípios arquiteturais

A arquitetura será organizada em três responsabilidades principais:

### 2.1 Parsers

Responsáveis por:

- Interpretar os formatos externos.
- Ler imagens, categorias e anotações.
- Converter coordenadas e representações geométricas.
- Preservar informações relevantes dos dados originais.
- Construir instâncias dos modelos internos.

Cada formato terá seu próprio parser.

### 2.2 Models

Responsáveis por:

- Representar os dados de maneira padronizada.
- Manter os atributos e relacionamentos dos elementos do dataset.
- Oferecer estruturas independentes dos formatos externos.

Os modelos não deverão conter lógica específica de leitura de COCO ou YOLO.

### 2.3 Auditors

Responsáveis por:

- Executar verificações de qualidade.
- Identificar inconsistências estruturais e geométricas.
- Identificar possíveis problemas de anotação.
- Produzir resultados padronizados para revisão.

Os auditors receberão os modelos internos, sem depender diretamente dos arquivos originais.

### 2.4 Fluxo geral

```text
Dataset COCO ──> COCO Parser ───────┐
                                   |
                                   v
                            Modelos internos
                                   |
                                   v
                              Audit Engine
                                   ^
                                   |
Dataset YOLO ──> YOLO Parser ──────┘
                                   |
                                   v
                              Audit Results
                                   |
                                   v
                             Quality Metrics
                                   |
                                   v
                             Quality Reports
```

O objetivo é permitir que os mesmos mecanismos de auditoria sejam utilizados em datasets provenientes de diferentes formatos.

## 3. Modelos internos

Os modelos internos representam os principais elementos de um dataset de segmentação.

A implementação inicial utiliza classes Python baseadas em `dataclasses`.

### 3.1 Category

**Arquivo:** `models/category.py`

Representa uma categoria existente no dataset.

Atributos:

| Atributo | Tipo | Descrição |
|---|---|---|
| `id` | `int` | Identificador da categoria dentro do dataset |
| `name` | `str` | Nome da categoria |
| `supercategory` | `str \| None` | Agrupamento superior, quando disponível |

Os IDs e nomes serão obtidos a partir dos dados de origem.

Não haverá categorias predefinidas ou dependência de um domínio específico.

Categorias com nomes semelhantes não serão unificadas automaticamente.

### 3.2 Image

**Arquivo:** `models/image.py`

Representa uma imagem pertencente ao dataset.

Atributos:

| Atributo | Tipo | Descrição |
|---|---|---|
| `id` | `int` | Identificador interno da imagem |
| `file_name` | `str` | Nome ou caminho relativo original da imagem |
| `width` | `int` | Largura em pixels |
| `height` | `int` | Altura em pixels |
| `resolved_path` | `Path \| None` | Caminho local completo, quando resolvido |

O caminho original será preservado separadamente do caminho local resolvido.

Essa separação evita dependência de diretórios ou nomes de batches específicos das exportações do CVAT.

A resolução dos caminhos será responsabilidade dos parsers.

A verificação da existência física dos arquivos poderá ser realizada por mecanismos específicos de auditoria.

### 3.3 Segmentation

**Arquivo:** `models/segmentation.py`

Representa a geometria de uma segmentação independentemente do formato de origem.

A implementação utiliza duas representações.

#### PolygonSegmentation

Representa a segmentação por meio de um ou mais polígonos.

Estrutura:

```python
polygons: list[list[tuple[float, float]]]
```

Cada polígono é uma sequência de pontos `(x, y)`.

As coordenadas serão expressas em pixels, relativas à imagem original.

A estrutura permite representar objetos compostos por múltiplas partes geométricas.

Atualmente, a estrutura armazena os polígonos, mas ainda não implementa validações geométricas, como interseções entre arestas, quantidade mínima de vértices ou coordenadas fora dos limites da imagem.

Também não possui uma semântica explícita para distinguir contornos externos de buracos geométricos. Essa necessidade deverá ser avaliada durante a implementação dos parsers e auditors.

#### MaskSegmentation

Representa uma segmentação por meio de uma máscara binária.

A implementação interna utiliza uma representação própria de RLE (Run-Length Encoding), independente das codificações específicas dos formatos externos.

Atributos:

| Atributo | Tipo | Descrição |
|---|---|---|
| `width` | `int` | Largura da máscara em pixels |
| `height` | `int` | Altura da máscara em pixels |
| `runs` | `tuple[int, ...]` | Sequência de comprimentos dos segmentos de pixels |

#### Convenção do RLE interno

A representação interna seguirá estas regras:

1. A máscara será percorrida em ordem de linhas (row-major), da esquerda para a direita e de cima para baixo.
2. A sequência começará contabilizando pixels de fundo (`0`).
3. Os segmentos alternarão entre pixels de fundo (`0`) e pixels de primeiro plano (`1`).
4. Cada valor de `runs` representará a quantidade de pixels consecutivos de um mesmo tipo.
5. A soma das contagens deverá corresponder a `width * height`.

Exemplo:

Máscara binária:

```text
0 1 1
0 0 1
```

Sequência de pixels em row-major:

```text
0 1 1 0 0 1
```

Representação interna:

```python
runs = (1, 2, 2, 1)
```

Caso a máscara comece diretamente com um pixel de primeiro plano, a primeira contagem poderá ser zero para manter a convenção de início pelo fundo.

A representação foi escolhida para desacoplar o modelo interno das codificações RLE externas.

**Estado atual:** a estrutura de armazenamento está implementada. As funções de codificação, decodificação e validação estrutural ainda serão desenvolvidas.

#### TypeAlias Segmentation

O tipo `Segmentation` representa a união das duas representações aceitas:

```python
Segmentation = PolygonSegmentation | MaskSegmentation
```

Esse tipo permite que outros modelos aceitem tanto segmentações poligonais quanto máscaras binárias, sem depender de uma implementação específica.

### 3.4 BoundingBox

**Arquivo:** `models/bounding_box.py`

Representa a caixa delimitadora de um objeto em uma imagem.

Atributos:

| Atributo | Tipo | Descrição |
|---|---|---|
| `x` | `float` | Coordenada horizontal do canto superior esquerdo |
| `y` | `float` | Coordenada vertical do canto superior esquerdo |
| `width` | `float` | Largura da caixa em pixels |
| `height` | `float` | Altura da caixa em pixels |

A representação utiliza coordenadas em pixels, com origem no canto superior esquerdo.

O modelo não valida atualmente limites, dimensões positivas ou compatibilidade com a imagem.

Essas verificações serão realizadas por mecanismos específicos do pipeline.

### 3.5 Annotation

**Arquivo:** `models/annotation.py`

Representa uma instância de objeto anotada em uma imagem.

Atributos:

| Atributo | Tipo | Descrição |
|---|---|---|
| `id` | `int` | Identificador da anotação dentro do dataset |
| `image_id` | `int` | Referência à imagem relacionada |
| `category_id` | `int` | Referência à categoria relacionada |
| `segmentation` | `Segmentation \| None` | Representação geométrica da segmentação |
| `bbox` | `BoundingBox \| None` | Caixa delimitadora, quando disponível |
| `area` | `float \| None` | Área da anotação, quando disponível |
| `is_crowd` | `bool \| None` | Informação de agrupamento, quando disponível |
| `attributes` | `dict[str, object]` | Metadados adicionais |

A classe relaciona uma imagem, uma categoria e uma representação geométrica de segmentação.

Os relacionamentos são armazenados por meio de identificadores (`image_id` e `category_id`), evitando duplicação dos objetos completos.

A segmentação e a bounding box são opcionais para permitir a representação de registros incompletos e a posterior identificação dessas situações pelas auditorias.

Valores indisponíveis deverão permanecer como `None`, quando aplicável, em vez de receber valores presumidos.

O campo `attributes` utiliza `default_factory` para garantir que diferentes anotações possuam dicionários independentes.

### 3.6 Dataset

**Arquivo:** `models/dataset.py`

Representa o conjunto completo de dados após a conversão para os modelos internos.

Atributos:

| Atributo | Tipo | Descrição |
|---|---|---|
| `images` | `list[Image]` | Imagens do dataset |
| `categories` | `list[Category]` | Categorias existentes |
| `annotations` | `list[Annotation]` | Anotações do dataset |
| `metadata` | `dict[str, object]` | Metadados gerais |

O modelo funciona como agregador das principais estruturas do dataset.

As listas e os metadados possuem valores padrão independentes por instância, utilizando `default_factory`.

O modelo não verifica atualmente a integridade dos relacionamentos entre imagens, categorias e anotações.

Essas verificações serão implementadas em etapas posteriores.

## 4. Padronização das coordenadas

Todas as representações geométricas internas deverão utilizar coordenadas em pixels, relativas às dimensões originais da imagem.

Convenção adotada:

- Origem no canto superior esquerdo.
- Eixo X crescente da esquerda para a direita.
- Eixo Y crescente de cima para baixo.
- Dimensões expressas em pixels.

### 4.1 Conversão COCO

O formato COCO utiliza coordenadas de polígonos em pixels.

Essas coordenadas poderão ser preservadas diretamente pelo parser após a interpretação dos dados.

A bounding box COCO utiliza:

```text
[x, y, width, height]
```

Essa representação corresponde diretamente ao modelo interno `BoundingBox`.

Para segmentações RLE, o parser deverá interpretar a codificação original do COCO e convertê-la para a representação interna.

Essa conversão deverá considerar que o RLE do COCO utiliza uma ordem de varredura diferente da convenção row-major adotada internamente.

Portanto, não será correto copiar diretamente as contagens do RLE COCO para `MaskSegmentation.runs`.

### 4.2 Conversão Ultralytics YOLO Segmentation

O formato Ultralytics YOLO Segmentation utiliza coordenadas normalizadas entre 0 e 1.

Cada linha do arquivo TXT representa uma instância de objeto e contém:

```text
class_id x1 y1 x2 y2 ... xn yn
```

O parser deverá:

1. Identificar a categoria por meio do `class_id`.
2. Interpretar os pares de coordenadas.
3. Obter as dimensões originais da imagem.
4. Converter as coordenadas normalizadas para pixels.

Conversão:

```text
x_pixel = x_normalizado * largura_da_imagem
y_pixel = y_normalizado * altura_da_imagem
```

Dessa maneira, os dois formatos alimentarão a mesma representação geométrica interna.

## 5. Formatos de entrada

### 5.1 COCO Segmentation

Será o primeiro formato a receber suporte.

O parser deverá interpretar:

- `images`
- `categories`
- `annotations`
- Segmentações poligonais
- Segmentações RLE
- Bounding boxes
- Áreas
- `iscrowd`
- Atributos adicionais

A resolução dos caminhos das imagens deverá utilizar um diretório raiz configurável, preservando o valor original de `file_name`.

### 5.2 Ultralytics YOLO Segmentation 1.0

Será o segundo formato a receber suporte.

O parser deverá interpretar:

- `data.yaml`
- Estrutura de diretórios.
- Imagens.
- Arquivos TXT de anotações.
- Identificadores de classes.
- Polígonos normalizados.
- Divisões do dataset, como train, val e test.

Informações não fornecidas pelo formato, como `is_crowd`, deverão permanecer indisponíveis (`None`), quando aplicável.

Bounding boxes poderão ser derivadas dos polígonos quando necessário, desde que a conversão seja definida e documentada.

### 5.3 YOLO 1.1

O formato clássico YOLO 1.1 representa anotações por bounding boxes.

Ele não será tratado como formato de segmentação poligonal, pois não fornece a geometria necessária para reconstruir máscaras de objetos.

## 6. Responsabilidades e validações

Uma separação importante da arquitetura será a diferença entre interpretação estrutural e auditoria de qualidade.

### Parsers

Responsáveis por:

- Ler os arquivos de entrada.
- Verificar se os dados possuem estruturas compatíveis com o formato esperado.
- Converter tipos e representações.
- Resolver caminhos.
- Construir os modelos internos.

Erros que impeçam a interpretação dos dados poderão gerar exceções específicas do parser.

### Models

Responsáveis por representar os dados.

Não deverão classificar anotações como corretas ou incorretas nem executar auditorias de qualidade.

Validações de integridade estrutural necessárias para a segurança das representações poderão ser adicionadas conforme a implementação evoluir.

### Auditors

Responsáveis por identificar problemas de qualidade.

Exemplos:

- Polígonos com geometria inválida.
- Coordenadas fora dos limites da imagem.
- Máscaras estruturalmente inconsistentes.
- Imagens sem anotações.
- Referências inválidas.
- Categorias desbalanceadas.
- Máscaras potencialmente pequenas ou grandes.

Uma ocorrência suspeita deverá ser sinalizada para revisão, não automaticamente classificada como erro definitivo.

A ausência de anotações também deverá ser analisada considerando que algumas imagens podem ser negativas de forma legítima.

## 7. Regras gerais da arquitetura

- Os modelos internos não deverão depender diretamente de COCO ou YOLO.
- Os identificadores serão únicos dentro de cada dataset, sem pressupor identificadores globais entre datasets diferentes.
- Categorias deverão preservar seus identificadores e nomes originais.
- Categorias semelhantes não serão unificadas automaticamente.
- Os caminhos das imagens deverão ser configuráveis.
- Informações ausentes deverão ser representadas corretamente.
- A geometria interna utilizará coordenadas em pixels.
- Os parsers serão responsáveis pelas conversões de formatos.
- Os auditors serão responsáveis pelas verificações de qualidade.
- Os resultados das auditorias deverão utilizar uma estrutura padronizada.

## 8. Organização dos diretórios

A estrutura planejada para a implementação dos componentes principais é:

```text
src/
└── quality_pipeline/
    ├── __init__.py
    │
    ├── models/
    │   ├── __init__.py
    │   ├── category.py
    │   ├── image.py
    │   ├── segmentation.py
    │   ├── bounding_box.py
    │   ├── annotation.py
    │   └── dataset.py
    │
    ├── parsers/
    │   ├── __init__.py
    │   ├── coco_parser.py
    │   └── yolo_segmentation_parser.py
    │
    └── auditors/
        ├── __init__.py
        ├── base.py
        └── audit_result.py
```

Os arquivos dos parsers e auditors representam a estrutura planejada e serão criados conforme a implementação avançar.

## 9. Estado atual da implementação

### Modelos implementados

| Componente | Estado |
|---|---|
| Category | Implementado inicialmente |
| Image | Implementado inicialmente |
| PolygonSegmentation | Implementado inicialmente |
| MaskSegmentation | Estrutura RLE implementada |
| BoundingBox | Implementado inicialmente |
| Annotation | Implementado inicialmente |
| Dataset | Implementado inicialmente |

Os modelos possuem testes automatizados iniciais.

A última validação registrada nesta etapa apresentou 15 testes aprovados.

Esses testes verificam principalmente armazenamento de atributos, valores opcionais e independência de coleções e metadados.

Eles ainda não representam uma validação completa das conversões dos formatos externos ou das regras geométricas.

### Componentes pendentes

| Componente | Estado |
|---|---|
| COCO Parser | Não implementado |
| YOLO Segmentation Parser | Não implementado |
| Codificação e decodificação do RLE interno | Pendente |
| Validações estruturais de máscaras | Pendentes |
| Audit Engine | Não implementado |
| AuditResult | Não implementado |
| Auditores | Não implementados |
| Métricas | Não implementadas |
| Relatórios | Não implementados |
| CLI | Não implementada |

## 10. Próximas decisões e validações

Durante as próximas etapas, deverão ser definidos e testados:

- Estratégia de codificação e decodificação das máscaras.
- Conversão correta entre RLE COCO e RLE interno.
- Tratamento de múltiplas partes de polígonos.
- Tratamento de buracos geométricos.
- Critérios para polígonos inválidos.
- Critérios para máscaras pequenas e grandes.
- Estratégia de resolução e validação dos caminhos das imagens.
- Preservação de metadados específicos dos formatos.
- Integridade dos relacionamentos entre imagens, categorias e anotações.

Essas decisões deverão preservar a independência dos modelos internos em relação aos formatos externos.

## 11. Decisões de escopo

A ferramenta será genérica e reutilizável em diferentes projetos de segmentação.

Não haverá categorias ou regras específicas para um domínio particular.

O sistema não utilizará um único indicador subjetivo de qualidade, como Dataset Health Score. Os resultados serão apresentados por meio de métricas individuais e ocorrências identificadas pelas auditorias.

A auditoria de Duplicate Annotations não faz parte do escopo definido.

A identificação de imagens duplicadas permanece como funcionalidade planejada.

Anotações suspeitas deverão ser sinalizadas para revisão humana, sem assumir automaticamente que estão incorretas.

---

## 12. Decisão arquitetural consolidada

Os modelos internos serão compartilhados por todos os formatos suportados.

Cada formato terá seu próprio parser, responsável por interpretar os dados externos e convertê-los para a representação interna padronizada.

Os auditores trabalharão exclusivamente com essa representação interna, permitindo reutilização das verificações e reduzindo a duplicação de código.

A arquitetura deverá evoluir de maneira incremental, preservando a separação entre interpretação, representação, auditoria e apresentação dos resultados.