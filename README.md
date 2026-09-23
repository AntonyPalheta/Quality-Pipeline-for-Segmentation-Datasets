# Quality Pipeline for Segmentation Datasets

## Objetivo

Desenvolver uma pipeline de auditoria, validação e melhoria da qualidade de datasets de segmentação exportados do CVAT.

O sistema tem como objetivo identificar automaticamente problemas que impactam diretamente o treinamento de modelos de visão computacional, gerar métricas de qualidade, calcular um **Dataset Health Score** e permitir correções automáticas ou assistidas.

A ferramenta busca reduzir erros de anotação, melhorar a qualidade dos datasets e aumentar a confiabilidade dos modelos treinados a partir desses dados.

---

# Problema

Em projetos de Visão Computacional, a qualidade do dataset é tão importante quanto a qualidade do modelo.

Problemas como:

- imagens sem anotação;
- classes desbalanceadas;
- polígonos inválidos;
- máscaras inconsistentes;
- objetos esquecidos;
- imagens duplicadas;
- labels incorretas;
- anotações redundantes;

podem degradar significativamente métricas como:

- mAP
- IoU
- Precision
- Recall

Em datasets grandes, realizar auditorias manuais torna-se inviável.

Este projeto propõe uma pipeline automatizada para auditoria e melhoria contínua da qualidade dos datasets utilizados em tarefas de segmentação.

---

# Visão Geral

O projeto será desenvolvido em etapas, iniciando com um MVP focado na detecção de problemas e evoluindo para mecanismos automáticos de correção.

Fluxo geral:

```text
CVAT Export
     ↓
Dataset Parser
     ↓
Audit Engine
     ↓
Health Scoring Engine
     ↓
Quality Report
     ↓
Dashboard
     ↓
Correction Engine
```

---

# Arquitetura

## 1. Dataset Parser

### Objetivo

Converter os arquivos exportados do CVAT em estruturas padronizadas para análise.

### Entradas

YOLO Segmentation:

```text
dataset/
├── images/
├── labels/
└── data.yaml
```

COCO:

```text
annotations.json
```

### Saídas

Estruturas internas do sistema:

```python
Dataset
Image
Annotation
Class
Mask
Polygon
BoundingBox
```

### Responsabilidades

- Ler datasets YOLO
- Ler datasets COCO
- Validar arquivos
- Indexar imagens
- Indexar anotações
- Normalizar formatos

---

## 2. Audit Engine

### Objetivo

Executar auditorias de qualidade nos dados.

### Responsabilidades

- Executar verificações independentes
- Detectar inconsistências
- Gerar alertas
- Produzir métricas

### Estrutura proposta

```text
auditors/
├── missing_annotations.py
├── class_balance.py
├── polygon_validator.py
├── duplicate_images.py
├── duplicate_annotations.py
├── mask_size.py
├── annotation_density.py
├── consistency.py
```

Cada auditor gera resultados no formato:

```python
AuditResult(
    severity="warning",
    category="mask_size",
    message="15 máscaras potencialmente inválidas"
)
```

---

## 3. Health Scoring Engine

### Objetivo

Transformar dezenas de métricas em uma nota final simples e compreensível.

Exemplo:

```text
Dataset Health Score

92/100
```

### Benefícios

- Facilita tomada de decisão
- Permite comparação entre datasets
- Permite acompanhar evolução da qualidade
- Cria indicador único para stakeholders

### Estrutura inicial da pontuação

```text
Completeness          25 pontos
Consistency           25 pontos
Annotation Quality    25 pontos
Dataset Balance       25 pontos
```

Exemplo:

```text
Completeness:        22/25
Consistency:         24/25
Annotation Quality:  23/25
Dataset Balance:     20/25

Total:               89/100
```

---

## 4. Quality Report

### Objetivo

Apresentar os resultados da auditoria.

### Formatos possíveis

```text
HTML
Markdown
JSON
CSV
```

### Exemplo

```text
DATASET REPORT

Total Images: 5200
Total Instances: 18432

Health Score: 91

Warnings:

- 12 imagens sem anotação
- 4 imagens duplicadas
- 7 máscaras pequenas
- classe radish sub-representada

Recommendations:

- revisar máscaras pequenas
- aumentar representatividade da classe radish
```

---

## 5. Dashboard

### Objetivo

Disponibilizar uma interface visual interativa.

### Tecnologias

- Streamlit
- Plotly
- Pandas

### Recursos

- Dataset Health Score
- Distribuição de classes
- Alertas
- Estatísticas globais
- Filtros
- Histórico de auditorias

---

## 6. Correction Engine

### Objetivo

Permitir correções assistidas ou automáticas.

### Exemplo

Detectado:

```text
15 imagens duplicadas
```

Sistema:

```text
Deseja remover?

[Sim]
[Não]
```

---

Detectado:

```text
100 labels vazias
```

Sistema:

```text
Mover para revisão?

[Sim]
[Não]
```

---

Detectado:

```text
apple → pear
```

Sistema:

```text
Aplicar correção em lote?

[Sim]
[Não]
```

---

# MVP

## 1. Dataset Statistics

### Objetivo

Gerar métricas básicas.

### Métricas

- total de imagens
- total de classes
- total de anotações
- objetos por classe
- objetos por imagem

---

## 2. Missing Annotations

### Detectar

- imagens sem labels
- labels vazias
- máscaras ausentes
- instâncias ausentes

---

## 3. Class Imbalance

### Detectar

- distribuição percentual por classe
- classes sub-representadas
- classes dominantes

### Exemplo

```text
Tomato: 85%
Potato: 10%
Radish: 5%
```

---

## 4. Polygon Validation

### Detectar

- self-intersections
- polígonos inválidos
- coordenadas fora da imagem
- polígonos degenerados

---

## 5. Small Masks

### Detectar

Máscaras com área muito pequena para sua classe.

### Possíveis causas

- erro de anotação
- objeto cortado
- máscara incompleta

---

## 6. Large Masks

### Detectar

Máscaras cobrindo porcentagens excessivas da imagem.

### Possíveis causas

- seleção incorreta
- inclusão de fundo

---

## 7. Duplicate Images

### Detectar

Imagens repetidas.

### Técnicas

- perceptual hash (pHash)
- image hashing
- embeddings

---

## 8. Duplicate Annotations

### Detectar

Mesma instância anotada múltiplas vezes.

### Estratégia

Calcular:

```text
IoU
```

Exemplo:

```text
IoU > 0.90
```

Possível duplicidade.

---

# Métricas de Auditoria

## Dataset Coverage

```text
Imagens anotadas / Imagens totais
```

Objetivo:

Medir completude do dataset.

---

## Annotation Density

```text
Instâncias / Imagem
```

Objetivo:

Medir densidade de objetos.

---

## Class Balance Score

Mede equilíbrio entre as classes.

Faixa:

```text
0 → Muito desbalanceado
1 → Muito balanceado
```

---

## Mask Area Distribution

Avalia distribuição das áreas das máscaras.

Detecta:

- outliers
- inconsistências

---

## Polygon Complexity

Mede quantidade de vértices.

Detecta:

- excesso de vértices
- simplificação excessiva

---

## Mask Coverage

Percentual da imagem ocupado pela máscara.

Detecta:

- máscaras muito pequenas
- máscaras muito grandes

---

## Annotation Consistency

Compara instâncias da mesma classe.

Exemplo:

```text
Tomato médio:
3000 px²

Tomato atual:
50 px²
```

Possível inconsistência.

---

## Empty Classes

Detecta classes cadastradas sem instâncias.

Exemplo:

```text
pear

Instâncias: 0
```

---

## Duplicate Rate

Percentual de duplicidade no dataset.

Exemplo:

```text
2.1%
```

---

# Dataset Health Score

## Objetivo

Transformar múltiplas métricas em um único indicador de qualidade.

### Fórmula inicial

```text
Health Score =

Completeness
+ Consistency
+ Annotation Quality
+ Dataset Balance
```

Resultado:

```text
0 - 100
```

---

## Exemplo

```text
Dataset Health Score

87/100

Problemas identificados:

- 8 imagens sem anotação
- 12 máscaras pequenas
- 5 imagens duplicadas
- classe radish sub-representada
```

---

## Benefícios

- Indicador simples para gestores
- Comparação entre versões do dataset
- Acompanhamento contínuo
- Métrica global para QA

---

# Roadmap

## Fase 1 - MVP

- [ ] Dataset Parser
- [ ] Dataset Statistics
- [ ] Missing Annotations Auditor
- [ ] Class Balance Auditor
- [ ] Polygon Validator
- [ ] Small/Large Masks Auditor
- [ ] Duplicate Images Auditor
- [ ] Dataset Health Score
- [ ] Exportação de relatórios

---

## Fase 2 - Dashboard

- [ ] Streamlit Dashboard
- [ ] Gráficos interativos
- [ ] Filtros por classe
- [ ] Histórico de auditorias
- [ ] Comparação entre datasets

---

## Fase 3 - Correction Engine

- [ ] Remoção de duplicatas
- [ ] Correção assistida
- [ ] Remapeamento de classes
- [ ] Validação em lote
- [ ] Workflow de revisão

---

## Fase 4 - Smart Audit

- [ ] Integração com detector de objetos
- [ ] Sugestão de objetos esquecidos
- [ ] Detecção automática de inconsistências
- [ ] Sugestão de correções baseada em IA

---

# Tecnologias Propostas

## Backend

- Python
- Pandas
- NumPy

## Visão Computacional

- OpenCV
- Shapely
- Scikit-image

## Dashboard

- Streamlit
- Plotly

## Dataset Formats

- YOLO Segmentation
- COCO

---

# Resultados Esperados

- Redução de erros de anotação
- Maior qualidade dos datasets
- Processos de QA padronizados
- Redução de retrabalho
- Maior confiabilidade dos modelos
- Ferramenta reutilizável entre projetos
- Criação de um indicador global de qualidade (Dataset Health Score)

---

# Visão de Longo Prazo

Transformar o projeto em uma plataforma interna de Quality Assurance para datasets de Visão Computacional, capaz de validar, monitorar, comparar e futuramente corrigir datasets exportados do CVAT antes do treinamento de modelos de segmentação.