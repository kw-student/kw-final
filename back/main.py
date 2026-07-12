from fastapi import FastAPI, HTTPException

from data import get_departments, get_college
from recommender import recommend as recommend_courses
from schemas import RecommendRequest, RecommendResponse

app = FastAPI(title="광운대 수강신청 추천 API")

@app.get("/departments", response_model=list[str])
def departments():
    return get_departments()

@app.post("/recommend", response_model=RecommendResponse)
def recommend(req: RecommendRequest):
    if get_college(req.department) is None:
        raise HTTPException(status_code=404, detail=f"'{req.department}'는 존재하지 않는 학과입니다.")

    courses, total_credits, message = recommend_courses(
        department=req.department,
        grade=req.grade,
        target_credits=req.target_credits,
        prefer_remote=req.prefer_remote,
        prefer_required=req.prefer_required,
    )

    return RecommendResponse(
        department=req.department,
        grade=req.grade,
        target_credits=req.target_credits,
        total_credits=total_credits,
        courses=courses,
        message=message,
    )
