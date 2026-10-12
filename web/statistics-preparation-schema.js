export const statisticsPreparationSchema = [
  {
    "id": "filter",
    "label": "Row filtering",
    "fields": [
      {
        "key": "match",
        "label": "Combine conditions",
        "type": "choice",
        "default": "all",
        "options": [
          [
            "all",
            "All conditions (AND)"
          ],
          [
            "any",
            "Any condition (OR)"
          ]
        ]
      },
      {
        "key": "conditions",
        "label": "Filter conditions",
        "type": "conditions",
        "default": "[{\"column\":\"0\",\"operator\":\"notBlank\",\"value\":\"\"}]",
        "options": [
          [
            "eq",
            "Number ="
          ],
          [
            "neq",
            "Number ≠"
          ],
          [
            "lt",
            "Number <"
          ],
          [
            "lte",
            "Number ≤"
          ],
          [
            "gt",
            "Number >"
          ],
          [
            "gte",
            "Number ≥"
          ],
          [
            "textEquals",
            "Text equals"
          ],
          [
            "textNotEquals",
            "Text does not equal"
          ],
          [
            "contains",
            "Text contains"
          ],
          [
            "startsWith",
            "Text starts with"
          ],
          [
            "endsWith",
            "Text ends with"
          ],
          [
            "blank",
            "Is blank"
          ],
          [
            "notBlank",
            "Is not blank"
          ]
        ]
      },
      {
        "key": "datasetName",
        "label": "New dataset name (blank = automatic)",
        "type": "text",
        "default": "",
        "preview": false
      }
    ]
  },
  {
    "id": "wideToLong",
    "label": "Wide → Long",
    "fields": [
      {
        "key": "ids",
        "label": "ID columns",
        "type": "columns",
        "default": "0"
      },
      {
        "key": "measures",
        "label": "Measurement columns",
        "type": "columns",
        "default": "auto"
      },
      {
        "key": "variableHeader",
        "label": "Variable column header",
        "type": "text",
        "default": "variable"
      },
      {
        "key": "valueHeader",
        "label": "Value column header",
        "type": "text",
        "default": "value"
      },
      {
        "key": "rowHeader",
        "label": "Automatic row ID header",
        "type": "text",
        "default": "row_id"
      }
    ]
  },
  {
    "id": "longToWide",
    "label": "Long → Wide",
    "fields": [
      {
        "key": "ids",
        "label": "ID columns",
        "type": "columns",
        "default": "0"
      },
      {
        "key": "variable",
        "label": "Variable column",
        "type": "column",
        "default": "1"
      },
      {
        "key": "value",
        "label": "Value column",
        "type": "column",
        "default": "-1"
      },
      {
        "key": "prefix",
        "label": "Column prefix",
        "type": "text",
        "default": ""
      },
      {
        "key": "duplicates",
        "label": "Duplicate ID / variable pairs",
        "type": "choice",
        "default": "error",
        "options": [
          [
            "error",
            "Error"
          ],
          [
            "first",
            "First value"
          ],
          [
            "last",
            "Last value"
          ],
          [
            "sum",
            "Sum"
          ],
          [
            "mean",
            "Mean"
          ]
        ]
      }
    ]
  },
  {
    "id": "recode",
    "label": "Recode variable",
    "fields": [
      {
        "key": "column",
        "label": "Source column",
        "type": "column",
        "default": "0"
      },
      {
        "key": "method",
        "label": "Recode method",
        "type": "choice",
        "default": "exact",
        "options": [
          [
            "exact",
            "Value mapping"
          ],
          [
            "intervals",
            "Numeric intervals"
          ]
        ]
      },
      {
        "key": "rules",
        "label": "Value mappings (old value, new value per line)",
        "type": "multiline",
        "default": "",
        "when": {
          "method": "exact"
        }
      },
      {
        "key": "cuts",
        "label": "Numeric cut points",
        "type": "text",
        "default": "",
        "when": {
          "method": "intervals"
        }
      },
      {
        "key": "groups",
        "label": "Group values (comma-separated)",
        "type": "text",
        "default": "0,1",
        "when": {
          "method": "intervals"
        }
      },
      {
        "key": "otherwise",
        "label": "Unmatched values",
        "type": "choice",
        "default": "keep",
        "options": [
          [
            "keep",
            "Keep original"
          ],
          [
            "blank",
            "Leave blank"
          ],
          [
            "value",
            "Use a value"
          ]
        ]
      },
      {
        "key": "otherwiseValue",
        "label": "Unmatched replacement value",
        "type": "text",
        "default": "",
        "when": {
          "otherwise": "value"
        }
      },
      {
        "key": "output",
        "label": "Recode output",
        "type": "choice",
        "default": "append",
        "options": [
          [
            "append",
            "Add a new column"
          ],
          [
            "replace",
            "Replace source column"
          ]
        ]
      },
      {
        "key": "header",
        "label": "New column header",
        "type": "text",
        "default": "recoded"
      }
    ]
  },
  {
    "id": "derive",
    "label": "Create derived variable",
    "fields": [
      {
        "key": "formula",
        "label": "Formula using column or header names",
        "type": "text",
        "default": ""
      },
      {
        "key": "header",
        "label": "New column header",
        "type": "text",
        "default": "derived"
      }
    ]
  }
];
