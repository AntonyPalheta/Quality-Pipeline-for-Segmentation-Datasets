
# Regras de Auditoria — Quality Pipeline for Segmentation Datasets

## 1. Objetivo

Este documento define os critérios utilizados pelos auditores do
Quality Pipeline for Segmentation Datasets para identificar problemas
de qualidade em datasets de segmentação.

Cada regra descreve:

- O problema que se deseja identificar.
- A condição necessária para que o problema seja reportado.
- A severidade atribuída.
- O elemento do dataset afetado.
- As limitações e condições de aplicação da verificação.

Este documento é a referência técnica para a implementação dos
auditores e deve permanecer alinhado ao comportamento do código
e dos testes automatizados.

As regras serão documentadas progressivamente, conforme cada
nível de auditoria for implementado e validado.

---

## 2. Organização dos níveis de auditoria

O sistema de auditoria está organizado em três níveis, que representam
diferentes dimensões da qualidade de um dataset de segmentação.

| Nível | Nome | Objetivo | Situação |
|---|---|---|---|
| 1 | Integridade estrutural | Verificar a consistência de identificadores, referências, arquivos e dimensões | Implementado |
| 2 | Integridade geométrica | Verificar a validade geométrica das anotações | Planejado |
| 3 | Integridade semântica | Identificar possíveis inconsistências relacionadas ao conteúdo visual e ao significado das anotações | Planejado |

Cada nível possui critérios próprios e será desenvolvido como uma
entrega independente.

As regras dos níveis 2 e 3 serão especificadas neste documento
quando suas respectivas implementações forem iniciadas.

---

# 3. Nível 1 — Integridade estrutural

## 3.1. Objetivo

O primeiro nível verifica a consistência estrutural dos elementos
que compõem o dataset.

O objetivo é identificar problemas que possam comprometer a
integridade das relações entre imagens, categorias e anotações,
além de verificar a disponibilidade dos arquivos e a compatibilidade
dimensional das máscaras RLE.

As verificações são determinísticas: cada problema é identificado
por meio de uma condição objetiva, sem necessidade de interpretação
visual da imagem.

O nível 1 é implementado pelo:

`DatasetIntegrityAuditor`

O auditor recebe uma instância do modelo interno `Dataset` e
retorna os problemas encontrados por meio de `AuditReport`.

## 3.2. Severidade

As regras implementadas neste nível utilizam a seguinte classificação:

| Severidade | Significado |
|---|---|
| ERROR | Violação objetiva de uma regra de integridade estrutural. |

A infraestrutura de resultados também oferece `WARNING` e `INFO`,
mas essas severidades não são utilizadas pelas sete regras atuais.

Um problema classificado como ERROR indica que uma condição
estrutural definida neste documento foi violada.

---

## 3.3. Regras implementadas

### AUD-001 — DUPLICATE_IMAGE_ID

**Nome:** Identificador de imagem duplicado.

**Objetivo:**

Identificar identificadores repetidos dentro da coleção de imagens
do dataset.

**Critério de identificação:**

Um problema é reportado quando o mesmo identificador aparece
mais de uma vez na coleção `Dataset.images`.

**Severidade:** ERROR.

**Elemento afetado:** Image.

**Exemplo:**

Duas imagens diferentes possuem o identificador `15`.

**Resultado esperado:**

Um único problema é registrado para o identificador duplicado,
informando quantas ocorrências foram encontradas.

**Limitações e observações:**

- A verificação considera somente a coleção de imagens.
- Um identificador igual ao de uma categoria ou anotação não
  caracteriza duplicidade.
- Se um identificador aparecer três ou mais vezes, será gerado
  um único problema para esse identificador, com a quantidade
  total de ocorrências.

---

### AUD-002 — DUPLICATE_CATEGORY_ID

**Nome:** Identificador de categoria duplicado.

**Objetivo:**

Identificar identificadores repetidos dentro da coleção de categorias
do dataset.

**Critério de identificação:**

Um problema é reportado quando o mesmo identificador aparece
mais de uma vez na coleção `Dataset.categories`.

**Severidade:** ERROR.

**Elemento afetado:** Category.

**Exemplo:**

Duas categorias diferentes utilizam o identificador `10`.

**Resultado esperado:**

Um único problema é registrado para o identificador duplicado,
informando a quantidade de ocorrências.

**Limitações e observações:**

- A verificação considera somente a coleção de categorias.
- Identificadores iguais em outras coleções não são considerados
  duplicados.
- Esta regra não tenta determinar se categorias com nomes
  semelhantes ou iguais representam a mesma classe.
- Não ocorre fusão ou alteração automática de categorias.

---

### AUD-003 — DUPLICATE_ANNOTATION_ID

**Nome:** Identificador de anotação duplicado.

**Objetivo:**

Identificar identificadores repetidos dentro da coleção de anotações
do dataset.

**Critério de identificação:**

Um problema é reportado quando o mesmo identificador aparece
mais de uma vez na coleção `Dataset.annotations`.

**Severidade:** ERROR.

**Elemento afetado:** Annotation.

**Exemplo:**

Duas anotações diferentes possuem o identificador `100`.

**Resultado esperado:**

Um único problema é registrado para o identificador duplicado,
informando a quantidade de ocorrências.

**Limitações e observações:**

- A verificação considera somente a coleção de anotações.
- O mesmo número pode existir em uma coleção de imagens ou
  categorias sem representar duplicidade.
- A regra não compara o conteúdo geométrico de duas anotações.
  Ela verifica exclusivamente a unicidade dos identificadores.

---

### AUD-004 — ANNOTATION_IMAGE_NOT_FOUND

**Nome:** Referência de imagem inexistente.

**Objetivo:**

Verificar se todas as anotações estão associadas a uma imagem
existente no dataset.

**Critério de identificação:**

Um problema é reportado quando o valor de `Annotation.image_id`
não corresponde ao identificador de nenhuma imagem existente
na coleção `Dataset.images`.

**Severidade:** ERROR.

**Elemento afetado:** Annotation.

**Exemplo:**

Uma anotação com ID `245` possui `image_id = 999`, mas não existe
nenhuma imagem com ID `999` no dataset.

**Resultado esperado:**

O relatório identifica a anotação afetada e informa o identificador
da imagem que não foi encontrado.

**Limitações e observações:**

- A existência da imagem é verificada pelo identificador interno.
- A regra não verifica se o objeto visual anotado realmente
  aparece na imagem.
- Caso existam imagens com o mesmo ID, a regra de duplicidade
  será reportada separadamente.
- A existência de uma imagem sem anotações não representa,
  por si só, um problema. Imagens negativas podem ser legítimas.

---

### AUD-005 — ANNOTATION_CATEGORY_NOT_FOUND

**Nome:** Referência de categoria inexistente.

**Objetivo:**

Verificar se todas as anotações utilizam categorias declaradas
no dataset.

**Critério de identificação:**

Um problema é reportado quando o valor de `Annotation.category_id`
não corresponde ao identificador de nenhuma categoria existente
na coleção `Dataset.categories`.

**Severidade:** ERROR.

**Elemento afetado:** Annotation.

**Exemplo:**

Uma anotação com ID `245` utiliza `category_id = 99`, mas não existe
nenhuma categoria com ID `99`.

**Resultado esperado:**

O relatório identifica a anotação afetada e informa o identificador
da categoria inexistente.

**Limitações e observações:**

- A verificação considera a existência do identificador, não o
  significado ou a correção visual do rótulo.
- Uma categoria existente com nome incorreto não será identificada
  por esta regra.
- A verificação de possíveis classes incorretas pertence ao
  nível de integridade semântica.

---

### AUD-006 — IMAGE_FILE_NOT_FOUND

**Nome:** Arquivo de imagem ausente.

**Objetivo:**

Verificar se os arquivos de imagem associados aos caminhos locais
resolvidos estão disponíveis no sistema de arquivos.

**Critério de identificação:**

Um problema é reportado quando:

1. A imagem possui um `resolved_path` definido.
2. O caminho não aponta para um arquivo existente, conforme
   a verificação `Path.is_file()`.

**Severidade:** ERROR.

**Elemento afetado:** Image.

**Exemplo:**

Uma imagem possui `resolved_path` apontando para
`data/images/image_15.jpg`, mas esse arquivo não existe.

**Resultado esperado:**

O relatório identifica a imagem afetada e apresenta o nome e
o caminho resolvido associados a ela.

**Limitações e observações:**

- Quando `resolved_path` é `None`, a verificação é ignorada.
  Nesse caso, o auditor não possui um caminho local para testar.
- A regra verifica a existência do arquivo, não se seu conteúdo
  é uma imagem válida.
- Não são realizadas verificações de corrupção, formato,
  resolução real ou possibilidade de decodificação.
- Um caminho que aponta para um diretório também não é
  considerado um arquivo válido.

---

### AUD-007 — MASK_DIMENSIONS_MISMATCH

**Nome:** Dimensões da máscara incompatíveis com a imagem.

**Objetivo:**

Verificar se as dimensões de uma máscara RLE correspondem
às dimensões da imagem associada à anotação.

**Critério de identificação:**

Um problema é reportado quando:

1. A anotação possui uma segmentação do tipo `MaskSegmentation`.
2. Existe exatamente uma imagem correspondente ao
   `Annotation.image_id`.
3. Pelo menos uma das dimensões da máscara é diferente da
   dimensão correspondente da imagem.

São comparados:

- `MaskSegmentation.width` com `Image.width`.
- `MaskSegmentation.height` com `Image.height`.

**Severidade:** ERROR.

**Elemento afetado:** Annotation.

**Exemplo:**

A imagem possui dimensões de `1920 × 1080`, enquanto sua
máscara RLE possui dimensões de `960 × 1080`.

A diferença de largura gera um problema de integridade.

**Resultado esperado:**

O relatório identifica a anotação e apresenta as dimensões
da máscara e da imagem para facilitar a análise.

**Limitações e observações:**

- A regra é aplicável somente às segmentações `MaskSegmentation`.
- Segmentações poligonais não possuem dimensões próprias
  armazenadas no modelo e não são verificadas por esta regra.
- A comparação não é realizada quando a imagem não existe.
- A comparação também é ignorada quando existem várias imagens
  com o mesmo identificador, pois a referência é ambígua.
- Esta regra verifica dimensões, não a correspondência visual
  entre os pixels da máscara e o objeto anotado.
- A integridade estrutural interna da sequência RLE é validada
  pelo próprio modelo `MaskSegmentation`.

---

## 3.4. Comportamentos gerais do Nível 1

Além das sete regras, o auditor segue algumas decisões gerais.

### Unicidade dos identificadores

Os identificadores são únicos dentro de cada coleção:

- `Dataset.images`
- `Dataset.categories`
- `Dataset.annotations`

Não existe exigência de que os IDs sejam globalmente únicos
entre todas as coleções.

### Imagens sem anotações

Uma imagem sem anotações não é considerada automaticamente
um erro.

Ela pode representar uma imagem negativa legítima, na qual
nenhum objeto de interesse está presente.

### Caminhos não resolvidos

Quando o parser não disponibiliza um `resolved_path`, o auditor
não classifica a imagem como ausente.

A ausência de um caminho disponível não comprova a ausência
do arquivo.

### Referências ambíguas

Quando existem IDs duplicados de imagens, uma anotação pode
ter uma referência ambígua.

Nesse caso, a duplicidade é reportada, mas não é realizada
a comparação dimensional da máscara RLE.

### Ausência de modificações automáticas

O auditor possui comportamento de leitura.

Ele identifica e reporta inconsistências, mas não altera,
remove ou corrige imagens, categorias ou anotações.

### Independência do formato de origem

O `DatasetIntegrityAuditor` trabalha com os modelos internos
do projeto, não diretamente com arquivos COCO ou YOLO.

Dessa maneira, diferentes parsers podem alimentar o mesmo
auditor, desde que convertam os dados para a estrutura interna
esperada.

---

## 3.5. Validações e evidências do Nível 1

O primeiro nível foi validado por três mecanismos complementares.

### Testes automatizados

Os testes verificam individualmente os comportamentos das
regras, incluindo situações válidas e inválidas.

### Dataset real

Foi executada uma auditoria sobre o dataset COCO utilizado
durante o desenvolvimento.

Resultado observado:

| Indicador | Resultado |
|---|---:|
| Imagens | 35 |
| Categorias | 69 |
| Anotações | 3003 |
| Problemas encontrados | 0 |

Todas as segmentações desse dataset eram poligonais.

### Dataset artificial

Foi criado um dataset controlado contendo uma inconsistência
para cada uma das sete regras.

Resultado observado:

| Indicador | Resultado |
|---|---:|
| Problemas esperados | 7 |
| Problemas identificados | 7 |
| Errors | 7 |
| Warnings | 0 |
| Info | 0 |

Todas as sete regras foram acionadas conforme esperado.

### Como executar a demonstração

A demonstração artificial está disponível em:

`examples/demo_dataset_integrity.py`

Para executá-la a partir da raiz do repositório:

```bash
python examples/demo_dataset_integrity.py
```

### Suíte automatizada

Na última execução registrada durante o desenvolvimento
do primeiro nível:

- 112 testes aprovados.
- Nenhum teste falhou.

Para executar novamente:

```bash
python -m pytest
```

---

# 4. Nível 2 — Integridade geométrica

**Situação: planejado, ainda não implementado.**

Este nível será responsável por avaliar a validade geométrica
das anotações.

O objetivo será identificar problemas relacionados à construção
e à consistência das geometrias utilizadas na segmentação.

Os critérios específicos serão definidos antes da implementação
deste nível e documentados aqui após sua validação.

---

# 5. Nível 3 — Integridade semântica

**Situação: planejado, ainda não implementado.**

Este nível será responsável por identificar possíveis inconsistências
entre o conteúdo visual das imagens e o significado das anotações.

Poderá envolver comparação com referências confiáveis, revisão humana,
análise de divergências entre anotadores e métodos de visão
computacional.

Os critérios específicos serão definidos antes da implementação
deste nível e documentados aqui após sua validação.

É importante distinguir problemas semanticamente suspeitos de erros
comprovados. Previsões de modelos de IA não serão tratadas
automaticamente como verdades absolutas.

---

## 6. Manutenção deste documento

Este documento deve evoluir junto com a implementação do projeto.

Sempre que um novo nível de auditoria for desenvolvido:

1. Definir os critérios das novas regras.
2. Implementar as verificações correspondentes.
3. Criar testes automatizados.
4. Validar os resultados com exemplos controlados.
5. Atualizar esta documentação.
6. Conferir se os critérios documentados correspondem ao código
   efetivamente implementado.

Nenhuma regra deve ser apresentada como concluída antes de
sua implementação e validação.

O objetivo é manter uma especificação técnica confiável,
reproduzível e alinhada ao comportamento real do
Quality Pipeline for Segmentation Datasets.
