import os
import logging
import requests

logger = logging.getLogger(__name__)

RAILWAY_GQL = "https://backboard.railway.app/graphql/v2"

REDEPLOY_MUTATION = """
mutation serviceInstanceRedeploy($environmentId: String!, $serviceId: String!) {
  serviceInstanceRedeploy(environmentId: $environmentId, serviceId: $serviceId)
}
"""


def restart_railway_service() -> bool:
    """Dispara un redeploy del servicio Railway configurado en variables de entorno."""
    token          = os.environ.get("RAILWAY_TOKEN", "")
    service_id     = os.environ.get("RAILWAY_SERVICE_ID", "")
    environment_id = os.environ.get("RAILWAY_ENV_ID", "")

    if not token or not service_id or not environment_id:
        logger.warning(
            "RAILWAY_TOKEN / RAILWAY_SERVICE_ID / RAILWAY_ENV_ID no configurados. "
            "Auto-restart omitido."
        )
        return False

    headers = {
        "Authorization": f"Bearer {token}",
        "Content-Type": "application/json",
    }
    payload = {
        "query": REDEPLOY_MUTATION,
        "variables": {"environmentId": environment_id, "serviceId": service_id},
    }

    try:
        resp = requests.post(RAILWAY_GQL, json=payload, headers=headers, timeout=15)
        resp.raise_for_status()
        data = resp.json()
        if "errors" in data:
            logger.error("Railway API errores: %s", data["errors"])
            return False
        logger.info("Redeploy Railway iniciado correctamente.")
        return True
    except requests.exceptions.RequestException as e:
        logger.error("Error en Railway API: %s", e)
        return False
