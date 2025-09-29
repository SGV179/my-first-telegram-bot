# ... [весь предыдущий код до функции create_initial_rewards] ...

async def create_initial_rewards():
    """Создает начальные награды в базе данных"""
    try:
        from database.connections import get_db
        from database.rewards_models import Reward
        
        db = next(get_db())
        
        # Проверяем, есть ли уже награды
        existing_rewards = db.query(Reward).count()
        if existing_rewards > 0:
            logger.info(f"✅ В базе уже есть {existing_rewards} наград")
            return
        
        # Создаем начальные награды
        initial_rewards = [
            {
                "name": "📚 Электронная книга",
                "description": "Эксклюзивные материалы по инвестициям и финансам",
                "cost": 50,
                "category": "digital"
            },
            {
                "name": "💼 Шаблон Excel",
                "description": "Полезные шаблоны для учета финансов и инвестиций",
                "cost": 30,
                "category": "digital"
            },
            {
                "name": "🎓 Видео-урок",
                "description": "Эксклюзивный видео-урок от эксперта",
                "cost": 100,
                "category": "digital"
            },
            {
                "name": "👑 Золотой статус",
                "description": "Специальный статус в сообществе на 1 месяц",
                "cost": 200,
                "category": "status"
            },
            {
                "name": "📊 Персональная консультация",
                "description": "15-минутная консультация с экспертом",
                "cost": 300,
                "category": "material"
            }
        ]
        
        for reward_data in initial_rewards:
            reward = Reward(**reward_data)
            db.add(reward)
        
        db.commit()
        logger.info(f"✅ Создано {len(initial_rewards)} начальных наград")
        
    except Exception as e:
        logger.error(f"❌ Ошибка создания начальных наград: {e}")

if __name__ == "__main__":
    asyncio.run(main())
