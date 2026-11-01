# Implementação Java: POO e LPR

## Escopo

Esta síntese reúne a documentação acadêmica de Programação Orientada a Objetos (POO) e Lógica de Programação (LPR) do primeiro ano. O material descreve uma implementação Java do CRUD administrativo Mottainai. Ele não descreve o backend Python/SQLite do hub de catálogo atual.

## Arquitetura documentada

A documentação técnica registra Java 21, Spring Boot 4.0.0 e Gradle. A aplicação separa responsabilidades entre:

- **Controller / Spring MVC:** recebe requisições e direciona respostas web ou REST;
- **DTO e validação:** transportam entradas e verificam formato e regras declaradas;
- **Service:** coordena regras de negócio, consultas e decisões de persistência;
- **DAO / repositório:** acessa PostgreSQL por JPA; consultas específicas também usam JDBC/JdbcTemplate;
- **Model / entidade:** representa os dados e seus relacionamentos;
- **JSP:** compõe as páginas web do painel.

O fluxo esperado é entrada HTTP → validação → regra de negócio → acesso a dados → resposta. A separação reduz dependência entre interface, regras e persistência.

## Práticas de POO e acesso a dados

- Manter atributos encapsulados e expor operações coerentes com a responsabilidade da classe.
- Separar representação do domínio, transporte de dados, regra de negócio e persistência.
- Usar parâmetros preparados para valores de consultas SQL.
- Fechar conexões e demais recursos de forma confiável, por exemplo com fechamento automático de recursos JDBC.
- Guardar configurações sensíveis fora do código-fonte e não versionar arquivos locais de segredo.

## Lógica, validação e falhas

A documentação de LPR destaca validações antes de persistir dados, regras de domínio, algoritmos auxiliares para validação e paginação, e tratamento explícito de erros. Exemplos incluem validação de CPF, consistência de status, paginação e distinção entre ausência de registro e falha inesperada.

Validação de formato e regra de negócio são camadas complementares: a primeira rejeita entradas inválidas; a segunda impede estados incompatíveis com o domínio. Respostas de erro devem orientar a correção sem expor dados internos.

## Verificação documentada

O material registra testes de sucesso e de falha com ferramentas do ecossistema Java, incluindo JUnit, Mockito e MockMvc. A evidência deve ser lida junto à versão de código correspondente; este resumo não afirma que os testes foram executados novamente durante a reorganização documental.

## Fonte e limites

A síntese deriva dos documentos finais de POO/Spring e LPR do acervo do primeiro ano e dos materiais introdutórios JDBC/DAO/Model. Detalhes de classes, tabelas, algoritmos e resultados devem ser confirmados no artefato técnico original antes de reutilização ou implementação.
