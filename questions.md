🌦️ Clima** (Open-Meteo, tempo real)
- "Qual a previsão do tempo em São Paulo?"
- "Está chovendo no Rio de Janeiro?"

**📚 RAG / FAQs e políticas** (dos docs em `vector_db/documents/`)
- "Qual o prazo para reembolso de um pedido?"
- "Posso cancelar um pedido que já foi enviado?"
- "Quais formas de pagamento vocês aceitam?"
- "Como faço para trocar meu e-mail cadastrado?"

**🗄️ SQL** (tabelas `clientes`/`pedidos` do `init.sql`)
- "Quantos clientes estão cadastrados?"
- "Quais pedidos estão com status 'processando'?"
- "Qual o valor total de pedidos da Ana Souza?"
- "Liste os clientes de São Paulo."

**🌐 Busca na web** (qualquer coisa fora do domínio interno, cai aqui via fallback ou roteamento direto)
- "Quem ganhou a última Copa do Mundo?"
- "O que é LangGraph?"