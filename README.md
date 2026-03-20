# 🛰️GEOSENSE
Documento de Arquitetura e Planejamento

Versão 1.0  —  2025

---

## **1. Visão Geral do Projeto**

O GeoSense tem como objetivo automatizar o monitoramento de rebanhos bovinos através de visão computacional e drones, permitindo que produtores rurais cataloguem, identifiquem e acompanhem cada animal individualmente sem intervenção manual. O sistema opera de forma offline em cada fazenda, com sincronização opcional para um servidor central.

### **Objetivos Principais**

- Capturar fotos do rebanho via drone e processar as imagens automaticamente  
- Detectar cada animal na foto e extrair sua silhueta precisa  
- Estimar tamanho e peso com base nas dimensões visuais  
- Gerar um ID único automático para cada animal novo (GEO-XXXX)  
- Permitir que cada fazenda defina suas próprias classificações de animais  
- Catalogar todos os dados em banco local por fazenda, com sync opcional  
- Oferecer interface simples e acessível ao produtor rural  

---

## **2. Fluxo Completo do Sistema**

| Etapa | O que acontece | Tecnologia |
|------|--------------|-----------|
| 1. Captura | Drone fotografa o rebanho de cima | Drone + armazenamento local |
| 2. Detecção | YOLO localiza cada animal na foto com bounding box | YOLOv8 (fine-tuned) |
| 3. Segmentação | SAM extrai a silhueta exata de cada animal detectado | Segment Anything Model |
| 4. Identificação | Sistema compara silhueta com banco — reconhece ou cria ID novo | Embeddings + similaridade cosseno |
| 5. Catalogação | Medidas, silhueta e histórico são salvos no banco | SQLite (local) + PostgreSQL (sync) |

---

## **3. Arquitetura Técnica**

### **Stack de Tecnologias**

| Camada | Tecnologia | Motivo da escolha |
|--------|-----------|------------------|
| Detecção | YOLOv8 (fine-tuned) | Rápido, preciso, eficiente para processamento de imagens |
| Segmentação | SAM (Segment Anything) | Extrai silhueta exata sem anotação manual |
| Identificação | Embeddings vetoriais | Reconhece o mesmo animal entre sessões pela aparência |
| Estimativa de peso | Regressão (scikit-learn) | Aprende relação medidas → peso com amostras reais |
| Banco local | SQLite | Zero configuração, um arquivo .db por fazenda, portátil |
| Banco central | PostgreSQL | Sync entre fazendas, backups e relatórios consolidados |
| Backend/API | FastAPI (Python) | Simples, rápido, integra direto com o código de visão |
| Interface | HTML/CSS/JS no navegador | Produtor acessa pelo browser, sem instalar nada |

---

### **Modelo 1 — Detecção (YOLOv8 fine-tuned)**

O modelo base do YOLO detecta animais genericamente. Para gado bovino fotografado de drone (ângulo superior), o modelo precisa ser ajustado com imagens reais do ambiente de uso.

- Dataset recomendado: 200 a 500 imagens anotadas com bounding box  
- Ferramenta de anotação: Roboflow — ótima escolha  
- Treinamento: Google Colab gratuito ou PC com GPU  
- Tempo estimado de treinamento: 2 a 4 horas  

---

### **Modelo 2 — Regressão de Peso**

Modelo simples que aprende a relação entre as dimensões visuais do animal e seu peso real. Precisa de amostras com peso conhecido.

- Entrada: comprimento (cm), largura (cm), área da silhueta (px²)  
- Saída: peso estimado em kg  
- Amostras necessárias: mínimo 30 a 50 animais pesados na balança  
- Algoritmo: Random Forest ou Regressão Linear (scikit-learn)  
- Erro esperado: ±10% a 15% — aceitável para decisão de abate  

---

## **4. Estrutura do Banco de Dados**

Arquitetura híbrida: SQLite local por fazenda + PostgreSQL central opcional.

### **Tabela: animal**

| Campo | Tipo | Descrição |
|------|------|----------|
| id | INTEGER PK | ID interno do sistema |
| codigo | TEXT | Código legível: GEO-0001, GEO-0002… |
| embedding | BLOB | Vetor da silhueta para reconhecimento futuro |
| silhueta_path | TEXT | Caminho da imagem da silhueta salva |
| data_cadastro | DATETIME | Data do primeiro registro |
| observacoes | TEXT | Anotações livres do produtor |

---

### **Tabela: classificacao_campo**

| Campo | Tipo | Descrição |
|------|------|----------|
| id | INTEGER PK | ID do campo de classificação |
| nome | TEXT | Nome do campo |
| tipo_valor | TEXT | Tipo: texto, numero, lista |
| opcoes | TEXT | JSON com opções |
| obrigatorio | INTEGER | 0 = opcional, 1 = obrigatório |

---

### **Tabela: animal_classificacao**

| Campo | Tipo | Descrição |
|------|------|----------|
| id | INTEGER PK | ID do registro |
| animal_id | INTEGER FK | Referência ao animal |
| campo_id | INTEGER FK | Referência ao campo |
| valor | TEXT | Valor preenchido |

---

### **Tabela: medicao**

| Campo | Tipo | Descrição |
|------|------|----------|
| id | INTEGER PK | ID da medição |
| animal_id | INTEGER FK | Referência ao animal |
| data | DATETIME | Data e hora |
| comprimento_cm | REAL | Comprimento |
| largura_cm | REAL | Largura |
| area_silhueta | REAL | Área |
| peso_estimado_kg | REAL | Peso estimado |
| confianca | REAL | Confiança YOLO |
| sessao_id | INTEGER FK | Sessão |

---

### **Tabela: sessao**

| Campo | Tipo | Descrição |
|------|------|----------|
| id | INTEGER PK | ID da sessão |
| data_inicio | DATETIME | Início |
| data_fim | DATETIME | Fim |
| fonte | TEXT | Origem |
| total_detectados | INTEGER | Total |
| altitude_m | REAL | Altitude |

---

### **4.1 Estratégia de Sincronização (SQLite → PostgreSQL)**

Cada fazenda opera de forma independente com SQLite local. Quando houver conexão, ocorre sincronização com PostgreSQL via PowerSync.

---

## **5. Como Funciona a Identificação Individual**

### **Primeira sessão — cadastro**

- YOLO detecta  
- SAM extrai silhueta  
- Geração de embedding  
- Comparação com banco  
- Se novo → gera GEO-XXXX  
- Salva dados  

### **Sessões seguintes — reconhecimento**

- Detecta → segmenta → embedding  
- Compara com banco  
- Match → atualiza  
- Sem match → novo ID  

---

## **6. Classificações Personalizadas por Fazenda**

Cada fazenda define seus próprios campos.

### **Exemplos**

- Fazenda A: Raça, Finalidade, Lote  
- Fazenda B: Raça, Idade estimada, Pasto  
- Fazenda C: Raça, Peso alvo, Observações  

---

## **7. Roadmap de Desenvolvimento**

| Fase | O que construir | Resultado |
|------|---------------|----------|
| 1 | YOLO detectando | IDs temporários |
| 2 | SAM silhueta | Silhuetas |
| 3 | SQLite + API | Persistência |
| 4 | Classificações | Cadastro flexível |
| 5 | Reconhecimento | Identificação |
| 6 | Peso | Estimativa |
| 7 | Interface | Dashboard |
| 8 | Sync | Multi-fazenda |
| 9 | Drone | Sistema completo |

---

## **8. Limitações e Pontos de Atenção**

- Peso: estimativa (±10-15%)  
- Reconhecimento: pode confundir animais similares  
- Ângulo: limita altura  
- Luz: influencia precisão  
- Dataset: quanto mais dados, melhor  

---

## **9. Próximos Passos Imediatos**

- Coletar fotos reais  
- Anotar 200 imagens no Roboflow  
- Treinar YOLOv8  
- Testar pipeline  
- Definir drone  
- Implementar banco  

---

## **10. Projetos de Referência**

- farmOS — farmos.org  
- livestock-tracker — github.com/DigiBanks99/livestock-tracker  
- PowerSync — powersync.com  
- YOLO + SAM livestock detection  
