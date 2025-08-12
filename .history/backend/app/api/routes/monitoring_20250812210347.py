@router.get("/status", response_model=List[HealthStatus])
async def get_services_status(db: AsyncSession = Depends(get_db)):
    """Get current status of all services"""
    
    # Get all services
    services_result = await db.execute(select(Service).where(Service.is_active == True))
    services = services_result.scalars().all()
    
    status_list = []
    for service in services:
        # Get latest check for this service
        check_result = await db.execute(
            select(ServiceCheck)
            .where(ServiceCheck.service_id == service.service_id)
            .order_by(desc(ServiceCheck.checked_at))
            .limit(1)
        )
        latest_check = check_result.scalar_one_or_none()
        
        if latest_check:
            status_list.append(HealthStatus(
                service_id=service.service_id,
                service_name=service.name,
                is_healthy=latest_check.is_healthy,
                status_code=latest_check.status_code or 0,
                response_time=latest_check.response_time,
                last_check=latest_check.checked_at,
                error_message=latest_check.error_message
            ))
    
    return status_list