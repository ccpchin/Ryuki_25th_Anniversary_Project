import random
import pygame
import sys

pygame.init()

WIDTH, HEIGHT = 1200, 750
screen = pygame.display.set_mode((WIDTH, HEIGHT))
pygame.display.set_caption("Kamen Rider Ryuki: Authentic Rider War Simulation")

BG_COLOR = (18, 18, 24)
PANEL_COLOR = (28, 30, 40)
TEXT_COLOR = (240, 240, 245)
ACCENT_RED = (220, 50, 50)
ACCENT_GOLD = (230, 190, 40)
ACCENT_BLUE = (50, 130, 240)
ACCENT_GREEN = (50, 200, 100)
BTN_HOVER = (70, 75, 95)
GRAY = (100, 100, 110)

font = pygame.font.SysFont("Arial", 16)
font_bold = pygame.font.SysFont("Arial", 18, bold=True)
font_title = pygame.font.SysFont("Arial", 22, bold=True)

class Environment:
    contract = {
        "DragRedder": "Ryuki", "DarkWing": "Knight", "VenoSnaker": "Ouja", 
        "Magnugiga": "Zolda", "MetalGelas": "Gai", "EvilDiver": "Raia", 
        "DestWilder": "Tiger", "GigaZelle": "Imperer", "VolCancer": "Scissors", 
        "BioGreeza": "Verde", "BlancWing": "Femme", "DragBlacker": "Ryuga", 
        "GoldPhoenix": "Odin", "PsycoRogue": ["Alternative", "AlternativeZero"]
    }
    mirrormonsters = {"Guld": 3, "Dragoons": 3, "Spiders": 6, "ZebraSkulls": 2, "Boarders": 2, "Biters": 2, "Kraken": 2, "BuzzStingers": 5, "Abyss": 2, "Wilders": 4}
    weeks = 50 

class Monster:
    def __init__(self, name, owner=None):
        self.name = name
        self.owner = owner  
        self.hunger = 0     
        self.is_rogue = False
        self.power = random.uniform(15, 30)

class Agent:
    def __init__(self, id, role="Civilian"):
        self.id = id
        self.role = role
        self.power = random.uniform(15, 35)  
        self.cards = 1                      
        self.has_survive = False            
        self.monster = None  
        self.title = None
        self.alive = True
        self.ally = None  
        # Lore: Civilians dissolve quickly; Riders have stability, amplified by Survive cards
        self.mirror_world_timer = random.randint(10, 20) if role == "Civilian" else 300
        self.x = random.randint(50, 800)
        self.y = random.randint(50, 700)

    def assign_odin(self):
        self.role = "Master"
        self.monster = Monster("GoldPhoenix", owner=self)
        self.title = "Odin"
        self.cards = 999
        self.has_survive = True
        self.power = 9999
        self.mirror_world_timer = 9999

    def assign_role(self, monster_name, title):
        self.role = "Rider"
        self.monster = Monster(monster_name, owner=self)
        self.title = title
        self.cards = 1  
        self.mirror_world_timer = 400  # Rider stability baseline

    def is_active(self):
        return self.alive and self.role in ("Rider", "Master")

    def clone(self):
        dup = Agent(self.id, self.role)
        dup.power = self.power
        dup.cards = self.cards
        dup.has_survive = self.has_survive
        dup.title = self.title
        dup.alive = self.alive
        dup.mirror_world_timer = self.mirror_world_timer
        dup.x = self.x
        dup.y = self.y
        if self.monster:
            m_dup = Monster(self.monster.name, dup)
            m_dup.hunger = self.monster.hunger
            m_dup.is_rogue = self.monster.is_rogue
            m_dup.power = self.monster.power
            dup.monster = m_dup
        return dup

class Simulation:
    def __init__(self):
        self.population = 250
        self.agents = [Agent(i) for i in range(self.population)]
        self.week = 0
        self.alternative = ["Alternative", "AlternativeZero"]
        self.wild_monsters = []
        self.simulation_over = False
        self.winner_text = "Paused - Press Play"
        self.history_states = []  
        self.civilian_pool_count = 200  # Abstracted civilian population to prevent total extinction glitch
        self.spawn_wild_monsters()
        self.assign_roles()
        self.assign_alliances()
        self.save_state()

    def spawn_wild_monsters(self):
        for m_name, count in Environment.mirrormonsters.items():
            for _ in range(count):
                self.wild_monsters.append(Monster(m_name))

    def assign_roles(self):
        self.agents[0].assign_odin()
        contract_items = [(m, r) for m, r in Environment.contract.items() if m != "GoldPhoenix"]
        random.shuffle(contract_items)
        
        available_indices = list(range(1, len(self.agents)))
        selected_indices = random.sample(available_indices, min(len(contract_items), len(available_indices)))
        
        for idx, (monster, rider) in zip(selected_indices, contract_items):
            if monster == "PsycoRogue":
                rider = self.alternative[0]
            self.agents[idx].assign_role(monster, rider)

    def assign_alliances(self):
        riders = [a for a in self.agents if a.role == "Rider"]
        for r in riders:
            potential_allies = [other for other in riders if other.id != r.id]
            if potential_allies and random.random() < 0.4:
                r.ally = random.choice(potential_allies)

    def save_state(self):
        snapshot = {
            "week": self.week,
            "agents": [a.clone() for a in self.agents],
            "wild_monsters": [Monster(m.name, None) for m in self.wild_monsters],
            "simulation_over": self.simulation_over,
            "winner_text": self.winner_text,
            "civilian_pool_count": self.civilian_pool_count
        }
        if len(self.history_states) >= 30:
            self.history_states.pop(0)
        self.history_states.append(snapshot)

    def step_backward(self):
        if len(self.history_states) > 1:
            self.history_states.pop()  
            prev = self.history_states[-1]  
            self.week = prev["week"]
            self.agents = [a.clone() for a in prev["agents"]]
            self.wild_monsters = [Monster(m.name, None) for m in prev["wild_monsters"]]
            self.simulation_over = prev["simulation_over"]
            self.winner_text = prev["winner_text"]
            self.civilian_pool_count = prev["civilian_pool_count"]

    def step(self):
        if self.simulation_over:
            return False

        self.week += 1      
        
        self.process_mirror_world_decay()
        self.mirror_monster_hunt_civilians()
        self.rider_vs_monster_combats()
        self.check_monster_hunger()

        # Variable simulation pacing: Dynamic thresholds
        active_riders = [a for a in self.agents if a.alive and a.role == "Rider"]
        
        # Survive Card Drop / Deck Expansion based on population threshold & time variability
        survive_threshold_week = random.randint(18, 24)
        if self.week == survive_threshold_week:
            if len(active_riders) >= 5:
                candidates_for_survive = random.sample(active_riders, min(2, len(active_riders)))
                for r in candidates_for_survive:
                    r.has_survive = True
                    r.cards += 2
                    r.power += 25  
                    r.mirror_world_timer = 9999  # Survive card grants absolute dimensional stability

        if self.week >= 40:
            self.trigger_endgame_monster_surge()
        
        if len(active_riders) <= 1 or self.week >= Environment.weeks:
            if active_riders:
                self.winner_text = f"Winner: {active_riders[0].title}"
            else:
                self.winner_text = "No Riders Survived!"
            self.conclude_rider_war()
            self.simulation_over = True
            self.save_state()
            return False  

        # Controlled PvP frequency with variable pacing
        active_agents = [a for a in self.agents if a.is_active() and a.title != "Odin"]
        random.shuffle(active_agents)
        pvp_chance = random.uniform(0.15, 0.25)
        if len(active_agents) >= 2 and random.random() < pvp_chance:  
            self.fight(active_agents[0], active_agents[1])

        # Lore: Odin intervenes rarely as an arbiter if simulation stalls or chaotic balance tips
        odin_agent = next((a for a in self.agents if a.title == "Odin" and a.alive), None)
        if odin_agent and len(active_agents) > 3 and random.random() < 0.05:
            target_rider = random.choice(active_agents)
            target_rider.alive = False  # Odin enforces Kanzaki's absolute rule

        self.save_state()
        return True

    def process_mirror_world_decay(self):
        for agent in self.agents:
            if not agent.alive:
                continue
            if agent.role == "Civilian":
                agent.mirror_world_timer -= 1
                if agent.mirror_world_timer <= 0:
                    agent.alive = False

    def mirror_monster_hunt_civilians(self):
        # Lore: Civilians are preyed upon globally by monsters rather than walking maps
        if self.civilian_pool_count > 20:
            loss = random.choices([0, 1, 2], weights=[0.6, 0.3, 0.1])[0]
            self.civilian_pool_count = max(10, self.civilian_pool_count - loss)

    def rider_vs_monster_combats(self):
        riders = [a for a in self.agents if a.is_active()]
        for rider in riders:
            if self.wild_monsters and random.random() < 0.2:
                monster = random.choice(self.wild_monsters)
                if rider.power + random.uniform(0, 15) >= monster.power:
                    rider.power += 1.0
                    if rider.monster:
                        rider.monster.hunger = 0  
                else:
                    rider.power -= 1.5
                    if rider.power <= 10:
                        rider.alive = False

    def trigger_endgame_monster_surge(self):
        for m in self.wild_monsters:
            m.power += 2.0
        for _ in range(1):
            random_type = random.choice(list(Environment.mirrormonsters.keys()))
            new_m = Monster(random_type)
            new_m.power += 8.0
            self.wild_monsters.append(new_m)

    def conclude_rider_war(self):
        self.wild_monsters.clear()
        for a in self.agents:
            if a.monster:
                a.monster = None

    def check_monster_hunger(self):
        riders = [a for a in self.agents if a.role in ("Rider", "Master") and a.alive]
        for r in riders:
            if not r.monster or r.monster.is_rogue:
                continue
            
            r.monster.hunger += 1
            # Lore: Starved contract monsters immediately turn rogue and execute their rider instantly
            hunger_limit = random.randint(6, 10)
            if r.monster.hunger >= hunger_limit:
                r.monster.is_rogue = True
                r.monster.owner = None
                r.alive = False  # Instant death from own contract monster betrayal
                self.wild_monsters.append(r.monster)

    def fight(self, a1, a2):
        if not a1.alive or not a2.alive:
            return
        score1 = a1.power + random.random()
        score2 = a2.power + random.random()
        if score1 > score2:
            self.resolve_kill(a1, a2)
        else:
            self.resolve_kill(a2, a1)

    def resolve_kill(self, winner, loser):
        if loser.title == "Odin":
            return
        
        loser.alive = False
        
        if loser.role == "Rider":
            winner.cards += 1
            winner.power += 3  
            
            if loser.ally and loser.ally.alive:
                loser.ally.cards += loser.cards
                loser.ally.power += 5
                if loser.has_survive and not loser.ally.has_survive:
                    loser.ally.has_survive = True
                    loser.ally.power += 20
                    loser.ally.mirror_world_timer = 9999

            if winner.monster:
                winner.monster.hunger = 0  

            if loser.monster and loser.monster.name == "PsycoRogue":
                self.reassign_alternative(loser.title)
            elif loser.monster:
                loser.monster.owner = None
                self.wild_monsters.append(loser.monster)

    def reassign_alternative(self, dead_title):
        if dead_title == "Alternative" and "AlternativeZero" in self.alternative:
            candidates = [a for a in self.agents if a.alive and a.role == "Civilian"]
            if not candidates:
                return
            new_agent = random.choice(candidates)
            new_agent.assign_role("PsycoRogue", "AlternativeZero")

sim = Simulation()
clock = pygame.time.Clock()
running = True
paused = True  

btn_play_rect = pygame.Rect(900, 530, 125, 36)
btn_back_rect = pygame.Rect(1035, 530, 125, 36)
btn_pause_rect = pygame.Rect(900, 580, 125, 36)
btn_restart_rect = pygame.Rect(1035, 580, 125, 36)

while running:
    screen.fill(BG_COLOR)

    mouse_pos = pygame.mouse.get_pos()
    mouse_clicked = False

    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            running = False
        elif event.type == pygame.KEYDOWN:
            if event.key == pygame.K_SPACE:
                paused = not paused
            elif event.key == pygame.K_r:
                sim = Simulation()
                paused = True
            elif event.key == pygame.K_LEFT:
                sim.step_backward()
        elif event.type == pygame.MOUSEBUTTONDOWN:
            if event.button == 1:
                mouse_clicked = True

    if btn_play_rect.collidepoint(mouse_pos) and mouse_clicked:
        paused = False
    if btn_back_rect.collidepoint(mouse_pos) and mouse_clicked:
        sim.step_backward()
    if btn_pause_rect.collidepoint(mouse_pos) and mouse_clicked:
        paused = not paused
    if btn_restart_rect.collidepoint(mouse_pos) and mouse_clicked:
        sim = Simulation()
        paused = True

    if not paused and not sim.simulation_over:
        sim.step()

    pygame.draw.rect(screen, PANEL_COLOR, (20, 20, 860, 710), border_radius=8)
    pygame.draw.rect(screen, GRAY, (20, 20, 860, 710), 2, border_radius=8)

    for agent in sim.agents:
        if not agent.alive:
            continue
        if agent.role == "Civilian":
            color = (70, 70, 80)
            size = 3
        elif agent.role == "Master":
            color = ACCENT_GOLD
            size = 8
        else:
            color = ACCENT_RED if agent.has_survive else ACCENT_BLUE
            size = 6
        pygame.draw.circle(screen, color, (agent.x, agent.y), size)

    sidebar_x = 900
    pygame.draw.rect(screen, PANEL_COLOR, (sidebar_x, 20, 280, 710), border_radius=8)
    pygame.draw.rect(screen, GRAY, (sidebar_x, 20, 280, 710), 2, border_radius=8)

    title_surf = font_title.render("RIDER WAR STATUS", True, ACCENT_GOLD)
    screen.blit(title_surf, (sidebar_x + 20, 40))

    active_riders = [a for a in sim.agents if a.role == "Rider" and a.alive]
    alive_civilians = sim.civilian_pool_count

    stats = [
        f"Week: {sim.week} / 50",
        f"Active Riders: {len(active_riders)}",
        f"Wild Monsters: {len(sim.wild_monsters)}",
        f"Civilian Pool: {alive_civilians}k",
        f"Status: {'PAUSED' if paused else 'RUNNING'}"
    ]

    y_offset = 90
    for stat in stats:
        surf = font_bold.render(stat, True, TEXT_COLOR)
        screen.blit(surf, (sidebar_x + 20, y_offset))
        y_offset += 30

    riders_title = font_title.render("Active Riders:", True, ACCENT_BLUE)
    screen.blit(riders_title, (sidebar_x + 20, y_offset + 10))
    y_offset += 45

    riders_list = [a for a in sim.agents if a.role in ("Rider", "Master") and a.alive]
    for r in riders_list[:10]:
        survive_tag = " [SURVIVE]" if r.has_survive else ""
        r_text = font.render(f"- {r.title} ({r.cards}c){survive_tag}", True, TEXT_COLOR)
        screen.blit(r_text, (sidebar_x + 20, y_offset))
        y_offset += 22

    if sim.simulation_over:
        win_surf = font_title.render(sim.winner_text, True, ACCENT_GREEN)
        screen.blit(win_surf, (sidebar_x + 20, 480))

    play_color = BTN_HOVER if btn_play_rect.collidepoint(mouse_pos) else (40, 45, 60)
    back_color = BTN_HOVER if btn_back_rect.collidepoint(mouse_pos) else (40, 45, 60)
    pause_color = BTN_HOVER if btn_pause_rect.collidepoint(mouse_pos) else (40, 45, 60)
    restart_color = BTN_HOVER if btn_restart_rect.collidepoint(mouse_pos) else (40, 45, 60)

    pygame.draw.rect(screen, play_color, btn_play_rect, border_radius=6)
    pygame.draw.rect(screen, GRAY, btn_play_rect, 1, border_radius=6)
    screen.blit(font.render("PLAY", True, TEXT_COLOR), (btn_play_rect.x + 42, btn_play_rect.y + 8))

    pygame.draw.rect(screen, back_color, btn_back_rect, border_radius=6)
    pygame.draw.rect(screen, GRAY, btn_back_rect, 1, border_radius=6)
    screen.blit(font.render("STEP BACK", True, TEXT_COLOR), (btn_back_rect.x + 20, btn_back_rect.y + 8))

    pygame.draw.rect(screen, pause_color, btn_pause_rect, border_radius=6)
    pygame.draw.rect(screen, GRAY, btn_pause_rect, 1, border_radius=6)
    screen.blit(font.render("PAUSE", True, TEXT_COLOR), (btn_pause_rect.x + 38, btn_pause_rect.y + 8))

    pygame.draw.rect(screen, restart_color, btn_restart_rect, border_radius=6)
    pygame.draw.rect(screen, GRAY, btn_restart_rect, 1, border_radius=6)
    screen.blit(font.render("RESTART", True, TEXT_COLOR), (btn_restart_rect.x + 30, btn_restart_rect.y + 8))

    pygame.display.flip()
    clock.tick(5)

pygame.quit()
sys.exit()