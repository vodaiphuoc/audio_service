from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from fastapi.responses import JSONResponse
from fastapi.templating import Jinja2Templates
from fastapi import Request


from database.sql.db import get_db
from user_router_components.schemas.user import (
    UserCreate, 
    UserLogin, 
    ResetPasswordRequest,
    VerifyOTPRequest
)
from user_router_components.user_utils.auth_service import AuthService


user_router = APIRouter()
templates = Jinja2Templates(directory="templates")

@user_router.post("/register")
def register(user:UserCreate, db:Session = Depends(get_db)):
    if AuthService.get_user_by_email(db, user.email):
        raise HTTPException(status_code=400, detail="Email đã được đăng ký")
    AuthService.create_user(db, user)
    return {"message": "Tạo người dùng thành công"}

@user_router.post("/login")
def login(user: UserLogin, db: Session = Depends(get_db)):
    try:
        token = AuthService.authenticate_user(db, user.email, user.password)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except PermissionError as e:
        raise HTTPException(status_code=403, detail=str(e))
    return {"access_token": token, "token_type": "bearer"}

@user_router.get("/dashboard")
def get_dashboard(request: Request):
    return templates.TemplateResponse("dashboard.html", {"request": request})

@user_router.post("/reset-password/request")
def forgot_password(request: ResetPasswordRequest, db: Session = Depends(get_db)):
    try:
        AuthService.handle_reset_password_request(request.email, db)
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    return {"message": "OTP đã được gửi đến email của bạn"}

@user_router.post("/reset-password/verify")
def verify_reset_password(request: VerifyOTPRequest,db: Session = Depends(get_db)):
    try:
        AuthService.handle_reset_password_verification(request.email,request.otp,request.new_password,db)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    return {"message": "Thay đổi mật khẩu thành công"}
