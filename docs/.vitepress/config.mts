import mathjax3 from "markdown-it-mathjax3";
import { defineConfig } from "vitepress";
import { withMermaid } from "vitepress-plugin-mermaid";

// https://vitepress.dev/reference/site-config
export default withMermaid(
  defineConfig({
    title: "CS Docs",
    base: "/books/",
    description: "Открытые занятия по компьютерным наукам",

    themeConfig: {
      outline: "deep",
      i18nRouting: true,
      socialLinks: [],
      nav: [
        { text: "Главная", link: "/" },
        {
          text: "Базы данных",
          link: "/databases/essentials/introduction/introduction",
        },
      ],

      sidebar: [
        {
          text: "Базы данных",
          items: [
            {
              text: "Основы баз данных",
              collapsed: false,
              items: [
                {
                  collapsed: false,
                  text: "Введение в базы данных",
                  items: [
                    {
                      text: "Введение в базы данных",
                      link: "/databases/essentials/introduction/introduction",
                    },
                    {
                      text: "Основные принципы функционирования СУБД",
                      link: "/databases/essentials/introduction/dbms-principles",
                    },
                  ],
                },
                {
                  collapsed: true,
                  text: "Реляционная модель данных",
                  items: [
                    {
                      text: "Реляционная модель данных",
                      link: "/databases/essentials/relational-model/relational-model",
                    },
                    {
                      text: "Основы проектирования баз данных",
                      link: "/databases/essentials/relational-model/erd-essentials",
                    },
                  ],
                },
                {
                  collapsed: true,
                  text: "Разработка информационно-логической модели БД",
                  link: "/databases/essentials/erd",
                },
              ],
            },
            {
              text: "Основы языка SQL",
              collapsed: true,
              items: [
                {
                  collapsed: true,
                  text: "Основы языка SQL",
                  items: [
                    {
                      text: "Типы данных и операторы СУБД PostgreSQL",
                      link: "/databases/sql/essentials/data-types",
                    },
                    {
                      text: "SQL-команды определения данных",
                      link: "/databases/sql/essentials/ddl",
                    },
                    {
                      text: "SQL-команды манипулирования данными",
                      link: "/databases/sql/essentials/dml",
                    },
                  ],
                },
                {
                  collapsed: true,
                  text: "Выборка данных",
                  items: [
                    {
                      text: "Отбор строк. Поиск по шаблону",
                      link: "/databases/sql/single-table-select/selections",
                    },
                    {
                      text: "Сортировка и группировка данных",
                      link: "/databases/sql/single-table-select/order-and-group",
                    },
                    {
                      text: "Разработка запросов на выборку данных",
                      link: "/databases/sql/single-table-select/task",
                    },
                  ],
                },
                {
                  collapsed: true,
                  text: "Многотабличные запросы",
                  items: [
                    {
                      text: "Комбинирование наборов данных",
                      link: "/databases/sql/multi-table-select/sets",
                    },
                    {
                      text: "Основы разработки многотабличных запросов",
                      link: "/databases/sql/multi-table-select/joins",
                    },
                    {
                      text: "Разработка многотабличных запросов",
                      link: "/databases/sql/multi-table-select/task",
                    },
                  ],
                },
                {
                  collapsed: true,
                  text: "Запросы с функциями",
                  link: "/databases/sql/functions",
                },

                {
                  collapsed: true,
                  text: "Запросы с подзапросами",
                  link: "/databases/sql/subqueries",
                },
                {
                  collapsed: true,
                  text: "Разработка таблиц",
                  link: "/databases/sql/create-table",
                },
                {
                  collapsed: true,
                  text: "Модификация данных",
                  link: "/databases/sql/data-modification",
                },
              ],
            },
            {
              text: "Основы организации и администрирования СУБД PostgreSQL",
              collapsed: true,
              items: [
                {
                  collapsed: true,
                  text: "Организация данных в СУБД PostgreSQL",
                  link: "/databases/administration/essentials",
                },
                {
                  collapsed: true,
                  text: "Работа со средствами администрирования СУБД PostgreSQL",
                  link: "/databases/administration/tooling",
                },
                {
                  collapsed: true,
                  text: "Управление доступом к объектам БД",
                  link: "/databases/administration/access-control",
                },
                {
                  collapsed: true,
                  text: "Конфигурирование сервера",
                  link: "/databases/administration/configuration",
                },
              ],
            },
            {
              text: "Нереляционные базы данных",
              collapsed: true,
              items: [
                {
                  collapsed: true,
                  text: "Основы NoSQL систем",
                  link: "/databases/nosql/essentials",
                },
                {
                  collapsed: true,
                  text: "Clickhouse",
                  items: [
                    {
                      collapsed: true,
                      text: "Основы",
                      link: "/databases/nosql/clickhouse/essentials",
                    },
                    {
                      collapsed: true,
                      text: "Структура базы данных",
                      link: "/databases/nosql/clickhouse/structure",
                    },
                    {
                      collapsed: true,
                      text: "Сравнение с PostgreSQL",
                      link: "/databases/nosql/clickhouse/postgres-compare",
                    },
                  ],
                },
                {
                  collapsed: true,
                  text: "Работа с колоночной СУБД Hbase",
                  link: "/databases/nosql/hbase",
                },
                {
                  text: "Работа с документной СУБД MongoDB",
                  collapsed: true,
                  items: [
                    {
                      collapsed: true,
                      text: "Основы",
                      link: "/databases/nosql/mongodb/essentials",
                    },
                    {
                      collapsed: true,
                      text: "Создание, редактирование и удаление данных. Индексы",
                      link: "/databases/nosql/mongodb/crud-and-indexes",
                    },
                    {
                      collapsed: true,
                      text: "Транзакции",
                      link: "/databases/nosql/mongodb/transactions",
                    },
                    {
                      collapsed: true,
                      text: "Сравнение с PostgreSQL",
                      link: "/databases/nosql/mongodb/postgres-compare",
                    },
                  ],
                },
                {
                  collapsed: true,
                  text: "Работа с большими объемами данных в реляционных и нереляционных СУБД",
                  link: "/databases/nosql/comparation",
                },
              ],
            },
            {
              text: "Разработка прикладных программ",
              collapsed: true,
              items: [
                {
                  collapsed: true,
                  text: "Разработка функций и триггеров",
                  link: "/databases/development/plpgsql",
                },
                {
                  text: "Python",
                  collapsed: true,
                  items: [
                    {
                      text: "Проектирование web-приложения для доступа к базе данных",
                      collapsed: true,
                      items: [
                        {
                          collapsed: true,
                          text: "Установка библиотек и подключение базы данных к приложению",
                          link: "/databases/development/python/design/database-connection",
                        },
                        {
                          collapsed: true,
                          text: "Основы работы в ПО Postman",
                          link: "/databases/development/python/design/postman",
                        },
                      ],
                    },
                    {
                      text: "Разработка web-приложения для доступа к базе данных",
                      collapsed: true,
                      items: [
                        {
                          collapsed: true,
                          text: "Разработка слоя репозиториев web-приложения",
                          link: "/databases/development/python/coding/repository",
                        },
                        {
                          collapsed: true,
                          text: "Разработка функционального слоя web-приложения",
                          link: "/databases/development/python/coding/service",
                        },
                        {
                          collapsed: true,
                          text: "Разработка слоя контроллеров web-приложения",
                          link: "/databases/development/python/coding/controller",
                        },
                      ],
                    },
                  ],
                },
                {
                  text: "JavaScript",
                  collapsed: true,
                  items: [
                    {
                      text: "Проектирование web-приложения для доступа к базе данных",
                      collapsed: true,
                      items: [
                        {
                          collapsed: true,
                          text: "Установка библиотек и подключение базы данных к приложению",
                          link: "/databases/development/js/design/database-connection",
                        },
                        {
                          collapsed: true,
                          text: "Основы работы в ПО Postman",
                          link: "/databases/development/js/design/postman",
                        },
                      ],
                    },
                    {
                      collapsed: true,
                      text: "Разработка web-приложения для доступа к базе данных",
                      items: [
                        {
                          collapsed: true,
                          text: "Разработка слоя репозиториев web-приложения",
                          link: "/databases/development/js/coding/repository",
                        },
                        {
                          collapsed: true,
                          text: "Разработка функционального слоя web-приложения",
                          link: "/databases/development/js/coding/service",
                        },
                        {
                          collapsed: true,
                          text: "Разработка слоя контроллеров web-приложения",
                          link: "/databases/development/js/coding/controller",
                        },
                      ],
                    },
                  ],
                },
              ],
            },
          ],
        },
      ],
    },
    vue: {
      template: {
        compilerOptions: {
          isCustomElement: (tag) => tag.startsWith("pglite-"),
        },
      },
    },
    vite: {
      optimizeDeps: {
        exclude: ["@electric-sql/pglite"],
      },
    },
    markdown: {
      config: (md) => {
        md.use(mathjax3);
      },
    },
  }),
);
