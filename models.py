from pydantic import BaseModel

class CorrectionRequest(BaseModel):
    exam_id: int
    student_id: int
    student_question: str

class CorrectionResponse(BaseModel):
    original: str
    student_answer: str
