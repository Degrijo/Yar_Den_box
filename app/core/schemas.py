greeting_schema = {
  "type": "object",
  "properties": {
    "event_type": {
      "const": "greeting"
    },
    "timestamp": {
      "type": "number"
    },
    "token": {
      "type": "string"
    }
  },
  "required": [
    "event_type",
    "timestamp",
    "token"
  ]
}

start_schema = {
  "type": "object",
  "properties": {
    "event_type": {
      "const": "start"
    },
    "timestamp": {
      "type": "number"
    },
  },
  "required": [
    "event_type",
    "timestamp"
  ]
}

answer_schema = {
  "type": "object",
  "properties": {
    "event_type": {
      "const": "answer"
    },
    "answer": {
      "type": "array",
      "items": [
        {
          "type": "object",
          "properties": {
            "questionId": {
              "type": "integer"
            },
            "answer": {
              "type": "string"
            }
          },
          "required": [
            "questionId",
            "answer"
          ]
        }
      ]
    },
    "timestamp": {
      "type": "number"
    },
  },
  "required": [
    "event_type",
    "answer",
    "timestamp"
  ]
}

vote_schema = {
  "type": "object",
  "properties": {
    "event_type": {
      "const": "voteList"
    },
    "votes": {
      "type": "array",
      "items": [
        {
          "type": "object",
          "properties": {
            "questionId": {
              "type": "integer"
            },
            "voteId": {
              "type": "integer"
            }
          },
          "required": [
            "questionId",
            "voteId"
          ]
        }
      ]
    },
    "timestamp": {
      "type": "number"
    },
  },
  "required": [
    "event_type",
    "votes",
    "timestamp"
  ]
}

EVENTS_SCHEMAS = (greeting_schema, start_schema, answer_schema, vote_schema)
