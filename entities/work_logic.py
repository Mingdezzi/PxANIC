import pygame
from settings import WORK_SEQ, TILE_SIZE

class WorkLogic:
    """
    플레이어와 NPC가 공통으로 사용하는 업무 로직 클래스
    """
    
    @staticmethod
    def get_work_target_tid(role, sub_role, day_count):
        """현재 날짜와 직업에 맞는 목표 타일 ID를 반환"""
        job_key = role if role == "DOCTOR" else sub_role
        if job_key in WORK_SEQ:
            seq = WORK_SEQ[job_key]
            # 날짜 기반 단계 결정 (1일차->0, 2일차->1, 3일차->2, 4일차->0...)
            return seq[(day_count - 1) % len(seq)]
        return None

    @staticmethod
    def complete_work(entity, gx, gy, day_count):
        """
        업무 완료 처리를 수행 (보상, 타일 변경, 쿨타임 등)
        """
        job_key = entity.role if entity.role == "DOCTOR" else entity.sub_role
        if job_key not in WORK_SEQ:
            return False
            
        # 1. 보상 및 소모
        entity.try_spend_ap(10)
        entity.coins += 1
        entity.daily_work_count += 1
        
        # 2. 타일 변경 (농부인 경우에만 수행)
        if entity.sub_role == 'FARMER':
            seq = WORK_SEQ['FARMER']
            day_idx = (day_count - 1) % len(seq)
            # 다음 단계의 타일 결정
            next_tile = seq[(day_idx + 1) % len(seq)]
            
            if entity.map_manager:
                entity.map_manager.set_tile(gx, gy, next_tile)
        
        # 3. 타일 쿨타임 적용
        if entity.map_manager:
            entity.map_manager.set_tile_cooldown(gx, gy, 3000)
            
        return True
