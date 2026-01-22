import math
import random

class RoleManager:
    @staticmethod
    def get_role_counts(total_players):
        """
        Returns required counts for special roles based on total players.
        Min 5 players assumed as per rule.
        Mafia: 20% (Round)
        Police: 20% (Round)
        Doctor: 1
        """
        if total_players < 5:
            # Fallback for testing with few players
            return {
                'MAFIA': 1,
                'POLICE': 1,
                'DOCTOR': 1
            }
            
        mafia = max(1, round(total_players * 0.2))
        police = max(1, round(total_players * 0.2))
        doctor = 1
        
        return {
            'MAFIA': mafia,
            'POLICE': police,
            'DOCTOR': doctor
        }

    @staticmethod
    def distribute_roles(participants):
        """
        Assigns roles to 'RANDOM' participants based on rules.
        Respects already manually assigned roles.
        Returns the modified list of participants.
        """
        total = len(participants)
        limits = RoleManager.get_role_counts(total)
        
        # 1. Count existing fixed roles
        current_counts = {'MAFIA': 0, 'POLICE': 0, 'DOCTOR': 0, 'CITIZEN': 0}
        random_candidates = []
        
        for p in participants:
            role = p.get('role', 'RANDOM')
            if role == 'RANDOM':
                random_candidates.append(p)
            else:
                if role in current_counts:
                    current_counts[role] += 1
                else: 
                    # Farmer/Miner/Fisher counts as Citizen for quota? 
                    # User said: "Citizen = Rest (Farmer/Miner/Fisher divided)"
                    # So specific jobs count as Citizens.
                    if role in ['FARMER', 'MINER', 'FISHER']:
                       current_counts['CITIZEN'] += 1
                    else:
                        # Unknown role? treat as catch-all
                        pass

        # 2. Determine needed roles
        start_roles_pool = []
        
        # Need Mafia?
        needed_mafia = max(0, limits['MAFIA'] - current_counts['MAFIA'])
        start_roles_pool.extend(['MAFIA'] * needed_mafia)
        
        # Need Police?
        needed_police = max(0, limits['POLICE'] - current_counts['POLICE'])
        start_roles_pool.extend(['POLICE'] * needed_police)
        
        # Need Doctor?
        needed_doctor = max(0, limits['DOCTOR'] - current_counts['DOCTOR'])
        start_roles_pool.extend(['DOCTOR'] * needed_doctor)
        
        # Remainder -> Citizen Jobs
        remaining_slots = len(random_candidates) - len(start_roles_pool)
        
        # Fill remainder with Citizen Jobs
        citizen_jobs = ['FARMER', 'MINER', 'FISHER']
        for i in range(remaining_slots):
            start_roles_pool.append(citizen_jobs[i % 3])
            
        # Shuffle pool
        random.shuffle(start_roles_pool)
        
        # 3. Assign
        # If pool is smaller than candidates (e.g. constraints exceeded), some will default to Citizen(Farmer)
        # If pool is larger (impossible by calc), we slice.
        
        for p in random_candidates:
            if start_roles_pool:
                new_role = start_roles_pool.pop(0)
                p['role'] = new_role
            else:
                # Fallback if logic drifted or manual exceeded limits taking up random slots
                p['role'] = 'FARMER' # Default fallback
                
        return participants
