# TESTE DEFINITIVO DE RENDERIZAÇÃO

## Instruções para o usuário:

1. Acesse: http://127.0.0.1:8000/avarias/882/

2. Na página, clique com botão direito → "Ver código-fonte da página" (ou Ctrl+U)

3. Procure por: "PROVA DE RENDERIZAÇÃO"

4. Me diga o que aparece:

   - Se aparecer: "<!-- PROVA DE RENDERIZAÇÃO: 2026-02-11 11:55:23 -->"
     (com uma data/hora real) = Django ESTÁ renderizando, problema é outra coisa
   
   - Se aparecer: "<!-- PROVA DE RENDERIZAÇÃO: {% now" Y-m-d H:i:s" %} -->"
     (com a tag Django literal) = Django NÃO está renderizando, problema é na view

## Por que este teste?

A tag `{% now %}` é processada pelo Django e mostra a data/hora atual.
Se aparecer processada no código-fonte, prova que o Django renderizou.
Se aparecer literal, prova que o navegador está recebendo o arquivo HTML puro.
