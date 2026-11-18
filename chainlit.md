# PlantaBot 🏭

Sistema especialista para supervisão, diagnóstico operacional e manutenção dos 8 equipamentos da planta industrial **PlantaView** (Bombas 1 e 2, Compressores 1 a 3, Motores 1 e 2 e Caldeira 1).

## O que você vê na conversa

- **Etapas de ferramenta:** cada consulta ao servidor MCP (sensores, alarmes, ordens de serviço) aparece como uma etapa que pode ser aberta, com os argumentos enviados e os dados devolvidos.
- **Raciocínio:** quando o modelo raciocina antes de responder, o texto fica num bloco recolhido.
- **Gráficos:** consultas de leituras de sensores trazem um gráfico com a faixa de operação (setpoints) e o valor lido de cada grandeza.
- **Origem da resposta:** o rodapé indica se a resposta veio do cache semântico ou do modelo, e quantas ferramentas foram consultadas.
- **Avisos:** o PlantaBot avisa quando as ferramentas devolvem dados simulados de contingência ou quando o servidor MCP está fora do ar.

O PlantaBot só responde sobre supervisão industrial, sensores, alarmes, equipamentos e manutenção da planta.
