{
  "version": 2,
  "builds": [
    {
      "src": "api/*.py",
      "use": "@vercel/python"
    }
  ],
  "routes": [
    {
      "src": "/api",
      "dest": "/api/api.py"
    },
    {
      "src": "/set-webhook",
      "dest": "/api/set-webhook.py"
    },
    {
      "src": "/webhook-info",
      "dest": "/api/webhook-info.py"
    },
    {
      "src": "/(.*)",
      "dest": "/api/index.py"
    }
  ]
}
