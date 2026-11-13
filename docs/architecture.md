## 1. Objetivo da arquitetura

O Quality Pipeline deverá suportar diferentes formatos de exportação de datasets de segmentação, inicialmente COCO e futuramente Ultralytics YOLO Segmentation.

Embora esses formatos representem informações semelhantes, eles possuem estruturas diferentes para armazenar imagens, categorias e anotações.

Para evitar dependência de um formato específico, o projeto utilizará uma representação interna padronizada.

Essa representação permitirá que os mecanismos de auditoria trabalhem independentemente do formato de origem dos dados.

## 2. Princípio arquitetural: independência de formato

A arquitetura será organizada em três responsabilidades principais:

- **Parsers:** interpretam os formatos externos e convertem seus dados para os modelos internos.
- **Models:** representam os dados de maneira padronizada, independentemente do formato de origem.
- **Auditors:** executam verificações de qualidade utilizando os modelos internos.

Fluxo geral:

```text
Dataset COCO ──> COCO Parser ───────┐
                                   │
                                   v
                            Modelos internos
                                   │
                                   v
                              Auditors
                                   ^
                                   │
Dataset YOLO ──> YOLO Parser ──────┘
```

O mecanismo de auditoria não deverá depender diretamente da estrutura dos arquivos COCO ou YOLO.

## 3. Modelos internos

Os modelos serão organizados em classes responsáveis por representar os principais elementos de um dataset de segmentação.

### 3.1 Category

Representa uma categoria existente no dataset.

Atributos:

- `id`: identificador da categoria dentro do dataset.
- `name`: nome da categoria.
- `supercategory`: agrupamento superior, quando disponível.

Os IDs e nomes serão obtidos a partir do dataset de origem. Não haverá categorias predefinidas ou dependência de um domínio específico.

### 3.2 Image

Representa uma imagem pertencente ao dataset.

Atributos:

- `id`: identificador interno da imagem.
- `file_name`: nome ou caminho relativo original da imagem.
- `width`: largura em pixels.
- `height`: altura em pixels.
- `resolved_path`: caminho local completo da imagem, quando resolvido.

O caminho original e o caminho local serão armazenados separadamente.

O projeto não deverá depender de nomes fixos de diretórios ou batches gerados pelo CVAT.

### 3.3 Segmentation

Representa a geometria da segmentação de maneira independente do formato de origem.

Serão suportadas duas representações principais:

**PolygonSegmentation**

Representa a segmentação por meio de um ou mais polígonos.

Cada polígono será composto por pontos com coordenadas `(x, y)` expressas em pixels, relativas à imagem original.

A representação permitirá múltiplas partes de um mesmo objeto.

**MaskSegmentation**

Representa a segmentação por meio de uma máscara binária, na qual os pixels indicam a presença ou ausência do objeto.

Máscaras poderão representar regiões desconectadas e buracos.

A representação interna não deverá depender da codificação RLE específica do COCO.

O parser será responsável por converter RLE para a representação interna de máscara.

A estratégia de armazenamento e decodificação das máscaras deverá considerar o consumo de memória e será validada durante a implementação.

### 3.4 BoundingBox

Representa a caixa delimitadora de uma anotação.

Atributos planejados:

- `x`: coordenada horizontal do canto superior esquerdo.
- `y`: coordenada vertical do canto superior esquerdo.
- `width`: largura da caixa.
- `height`: altura da caixa.

Todas as coordenadas serão expressas em pixels.

A bounding box será opcional dentro de uma anotação, pois nem todos os formatos fornecem esse dado diretamente.

### 3.5 Annotation

Representa uma instância de objeto anotada em uma imagem.

Atributos planejados:

- `id`: identificador único da anotação dentro do dataset.
- `image_id`: referência à imagem relacionada.
- `category_id`: referência à categoria relacionada.
- `segmentation`: representação geométrica da anotação.
- `bbox`: bounding box, quando disponível.
- `area`: área da anotação, quando disponível.
- `is_crowd`: indica se a anotação representa um agrupamento de objetos, quando essa informação existir.
- `attributes`: metadados adicionais associados à anotação.

A segmentação será representada pelo modelo `Segmentation`, sem armazenar diretamente estruturas específicas de COCO ou YOLO.

Informações ausentes na origem deverão permanecer como não disponíveis (`None`) quando aplicável, em vez de receber valores presumidos.

### 3.6 Dataset

Representa o conjunto completo de dados após a conversão para os modelos internos.

Deverá reunir:

- Imagens (`Image`).
- Categorias (`Category`).
- Anotações (`Annotation`).
- Metadados gerais, quando disponíveis.

## 4. Padronização das coordenadas

As representações geométricas internas utilizarão coordenadas em pixels, relativas às dimensões originais da imagem.

O sistema de coordenadas adotará:

- Origem no canto superior esquerdo.
- Eixo X crescente da esquerda para a direita.
- Eixo Y crescente de cima para baixo.

### Conversão COCO

As coordenadas dos polígonos COCO já são expressas em pixels e poderão ser utilizadas diretamente, após a interpretação pelo parser.

Representações RLE deverão ser convertidas para máscaras internas.

### Conversão YOLO Segmentation

O formato Ultralytics YOLO Segmentation utiliza coordenadas normalizadas entre 0 e 1.

O parser deverá converter essas coordenadas para pixels:

```text
x_pixel = x_normalizado * largura_da_imagem

y_pixel = y_normalizado * altura_da_imagem
```

Dessa maneira, os modelos internos utilizarão uma única convenção geométrica.

## 5. Formatos de entrada

### 5.1 COCO

Será o primeiro formato implementado.

O parser deverá interpretar:

- `images`
- `categories`
- `annotations`
- Polígonos
- RLE
- Bounding boxes
- Áreas
- Atributos adicionais

### 5.2 Ultralytics YOLO Segmentation 1.0

Será o próximo formato a receber suporte.

O parser deverá interpretar:

- `data.yaml`
- Diretórios de imagens e anotações.
- Arquivos TXT com coordenadas dos polígonos.
- Identificadores de classes.
- Coordenadas normalizadas.
- Divisões do dataset, como train, val e test.

As dimensões das imagens poderão ser obtidas diretamente dos arquivos de imagem.

Como esse formato não fornece alguns atributos existentes no COCO, como `area` e `iscrowd`, eles permanecerão indisponíveis quando não puderem ser obtidos com segurança.

### 5.3 YOLO 1.1

O formato clássico YOLO 1.1 representa anotações por bounding boxes e não será utilizado como formato de entrada para o parser de segmentação.

O suporte futuro a outros formatos deverá respeitar a separação entre parsers e modelos internos.

## 6. Regras gerais de implementação

- Os modelos internos não deverão depender de estruturas específicas do COCO ou YOLO.
- Os IDs serão únicos dentro de cada dataset, sem pressupor identificadores globais entre datasets diferentes.
- Os parsers serão responsáveis por atribuir IDs internos quando o formato de origem não fornecer identificadores.
- Categorias deverão preservar seus nomes e identificadores originais, sem unificação automática de categorias semelhantes.
- Os caminhos das imagens deverão ser resolvidos de maneira configurável.
- A ausência de informações deverá ser representada corretamente, sem presumir valores.
- Os modelos serão responsáveis pela representação dos dados, enquanto as verificações de qualidade serão implementadas nos auditors.

## 7. Benefícios esperados

Essa arquitetura busca proporcionar:

- Reutilização das auditorias entre diferentes formatos.
- Redução da duplicação de código.
- Facilidade para adicionar novos formatos.
- Separação clara entre leitura, representação e validação.
- Maior flexibilidade para diferentes domínios e tipos de datasets.
- Facilidade de manutenção e evolução do projeto.

## 8. Pontos que serão validados durante a implementação

Algumas decisões de baixo nível ainda deverão ser testadas:

- Estratégia de armazenamento e decodificação de máscaras, considerando consumo de memória.
- Tratamento de geometrias com múltiplas partes e particularidades de buracos.
- Estratégia para obtenção ou cálculo de bounding boxes.
- Preservação de metadados específicos dos formatos.
- Resolução de caminhos em diferentes estruturas de exportação.

Esses pontos deverão ser resolvidos sem comprometer o princípio de independência dos modelos em relação aos formatos externos.

---

**Decisão arquitetural:** os modelos internos serão compartilhados por todos os formatos suportados. Cada formato terá seu próprio parser, responsável por converter seus dados para a representação interna padronizada.