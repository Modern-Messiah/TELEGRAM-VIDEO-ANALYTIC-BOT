-- Удаляем таблицы если существуют
DROP TABLE IF EXISTS video_snapshots CASCADE;
DROP TABLE IF EXISTS videos CASCADE;

-- Таблица с итоговой статистикой видео
CREATE TABLE videos (
    id VARCHAR(255) PRIMARY KEY,
    creator_id VARCHAR(255) NOT NULL,
    video_created_at TIMESTAMP WITH TIME ZONE NOT NULL,
    views_count INTEGER DEFAULT 0,
    likes_count INTEGER DEFAULT 0,
    comments_count INTEGER DEFAULT 0,
    reports_count INTEGER DEFAULT 0,
    created_at TIMESTAMP WITH TIME ZONE,
    updated_at TIMESTAMP WITH TIME ZONE
);

-- Таблица с почасовыми снапшотами
CREATE TABLE video_snapshots (
    id VARCHAR(255) PRIMARY KEY,
    video_id VARCHAR(255) NOT NULL,
    views_count INTEGER DEFAULT 0,
    likes_count INTEGER DEFAULT 0,
    comments_count INTEGER DEFAULT 0,
    reports_count INTEGER DEFAULT 0,
    delta_views_count INTEGER DEFAULT 0,
    delta_likes_count INTEGER DEFAULT 0,
    delta_comments_count INTEGER DEFAULT 0,
    delta_reports_count INTEGER DEFAULT 0,
    created_at TIMESTAMP WITH TIME ZONE,
    updated_at TIMESTAMP WITH TIME ZONE,
    FOREIGN KEY (video_id) REFERENCES videos(id) ON DELETE CASCADE
);

-- Индексы для ускорения запросов
CREATE INDEX idx_videos_creator_id ON videos(creator_id);
CREATE INDEX idx_videos_created_at ON videos(video_created_at);
CREATE INDEX idx_videos_views ON videos(views_count);
CREATE INDEX idx_snapshots_video_id ON video_snapshots(video_id);
CREATE INDEX idx_snapshots_created_at ON video_snapshots(created_at);

-- Комментарии к таблицам
COMMENT ON TABLE videos IS 'Итоговая статистика по каждому видео';
COMMENT ON TABLE video_snapshots IS 'Почасовые снапшоты статистики для отслеживания динамики';
