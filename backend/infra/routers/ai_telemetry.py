from fastapi import APIRouter, Depends

from application.use_cases import TelemetriaUseCase
from infra.deps import get_telemetria
from infra.security import verify_token

router = APIRouter(prefix="/api/v1/ai", tags=["IA Telemetria"])


@router.get("/telemetry")
def get_telemetry(
    _: str = Depends(verify_token),
    use_case: TelemetriaUseCase = Depends(get_telemetria),
):
    """
    Endpoint exclusivo para consumo por agentes de IA externos.

    Retorna dados formatados e limpos otimizados para LLMs:
    - summary: métricas agregadas (total, taxa de sucesso, tempo médio)
    - scripts_ranking: scripts mais executados com taxa de sucesso individual
    - recent_history: últimas 10 execuções com parâmetros e status
    - health_score: pontuação geral de saúde (0-100)
    - context_for_llm: resumo textual pronto para uso em prompts
    """
    return use_case.execute()
