-- user-service
CREATE DATABASE IF NOT EXISTS user_service
    DEFAULT CHARACTER SET  utf8mb4
    DEFAULT COLLATE utf8mb4_unicode_ci;
USE user_service;

CREATE TABLE user (
	idx	        bigint	NOT NULL AUTO_INCREMENT PRIMARY KEY,
	token_id	int	NOT NULL,
	last_name	varchar(3)	NOT NULL,
	first_name	varchar(3)	NOT NULL,
	user_id	    varchar(10)	NOT NULL,
	pw	        varchar(100)	NOT NULL,
	email	    varchar(20)	NOT NULL,
	tel	        smallint	NOT NULL,
	birth	    date	NOT NULL,
    gender	    tinyint	    NOT NULL	COMMENT '남(1) 여(2)',
	team	    varchar(10)	NULL,
	create_at	datetime	NOT NULL DEFAULT CURRENT_TIMESTAMP,
	updated_at	datetime	NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
	is_staff	tinyint	NOT NULL	COMMENT '관리자, 사용자',
	is_active	tinyint	NOT NULL	COMMENT '활성/비활성',
	last_login	datetime	NOT NULL
);

-- board-service
CREATE DATABASE IF NOT EXISTS board_service
    DEFAULT CHARACTER SET  utf8mb4
    DEFAULT COLLATE utf8mb4_unicode_ci;
USE board_service;


CREATE TABLE post (
	idx	            bigint	NOT NULL AUTO_INCREMENT PRIMARY KEY, 
	token_id	    int	NOT NULL,
	user_id	        varchar(128)	NOT NULL,
	category	    varchar(10)	NOT NULL	COMMENT '자유글, 동행, 거래',
	title	        varchar(100)	NOT NULL,
	content	        LONGTEXT	NOT NULL,
	views	        int	NOT NULL DEFAULT 0,
	created_at	    datetime	NOT NULL DEFAULT CURRENT_TIMESTAMP,
	updated_at	    datetime	NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
	is_pinned	    tinyint(1)	NOT NULL DEFAULT 0,
	pin_category	varchar(20)	NOT NULL,
	pin_type	    varchar(20)	NOT NULL	COMMENT 'pin_category가 category 값일 경우 어떤 게시판에 고정 인지에 대한 값'
);


CREATE TABLE comment (
	idx	            bigint	NOT NULL AUTO_INCREMENT PRIMARY KEY, 
	post_id     	bigint	NOT NULL,
	content     	LONGTEXT	NOT NULL,
	user_id	        varchar(128)	NOT NULL,
    created_at	    datetime	NOT NULL DEFAULT CURRENT_TIMESTAMP,
	updated_at	    datetime	NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    CONSTRAINT fk_comment_post FOREIGN KEY (post_id) REFERENCES post(idx)
    ON DELETE CASCADE ON UPDATE CASCADE
);

-- news-service
CREATE DATABASE IF NOT EXISTS news_service
    DEFAULT CHARACTER SET  utf8mb4
    DEFAULT COLLATE utf8mb4_unicode_ci;
USE news_service;

CREATE TABLE news (
	idx	    	bigint	        NOT NULL AUTO_INCREMENT PRIMARY KEY,
	title		varchar(200)	NOT NULL,
	keyword		varchar(100)	NULL,
	link		varchar(100)	NOT NULL,
	crawl_date 	date			NOT NULL,
	created_at	datetime	NOT NULL
);

-- info-service
CREATE DATABASE IF NOT EXISTS info_service
    DEFAULT CHARACTER SET  utf8mb4
    DEFAULT COLLATE utf8mb4_unicode_ci;
USE info_service;

CREATE TABLE team (
	idx	        tinyint	    NOT NULL AUTO_INCREMENT PRIMARY KEY,
	t_name	varchar(10)	    NOT NULL,
	code	    varchar(10)	NOT NULL UNIQUE KEY,
	city	    varchar(10)	NOT NULL,
	stadium	    varchar(20)	NOT NULL
);

CREATE TABLE info (
	idx	        int	            NOT NULL AUTO_INCREMENT PRIMARY KEY,
	p_name	    varchar(10)	    NOT NULL,
	p_number	smallint	    NOT NULL,
	p_position	varchar(5)	    NOT NULL,
	height_cm	char(5)	        NOT NULL,
	weight_kg	decimal(5,1)	NOT NULL,
	birth	    date	        NOT NULL,
	p_info	    varchar(10)     NOT NULL	COMMENT '우/좌',
	team_id	    tinyint	        NOT NULL,
    created_at   DATETIME       NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at   DATETIME       NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    UNIQUE KEY uq_team_number (team_id, p_number, p_name)
    CONSTRAINT fk_info_team FOREIGN KEY (team_id) REFERENCES team(idx)
    ON DELETE CASCADE ON UPDATE CASCADE
);

-- event-service
CREATE DATABASE IF NOT EXISTS event_service
    DEFAULT CHARACTER SET  utf8mb4
    DEFAULT COLLATE utf8mb4_unicode_ci;
USE event_service;

CREATE TABLE result (
	idx	            bigint	        NOT NULL AUTO_INCREMENT PRIMARY KEY,
	match_date	    date	    NOT NULL,
	start_time	    varchar(5)	NULL	    COMMENT '경기취소의 경우 NULL',
	away_team	    varchar(5)	NOT NULL,
	at_score	    tinyint	    NULL        COMMENT '경기취소의 경우 NULL',
	home_team	    varchar(5)	NOT NULL,
	ht_score	    tinyint	    NULL        COMMENT '경기취소의 경우 NULL',
	match_status	varchar(5)	NOT NULL	COMMENT '종료, 경기취소, 경기전',
	stadium	        varchar(30)	NULL        COMMENT '경기취소의 경우 NULL',
	winner	        varchar(5)	NULL        COMMENT '경기취소의 경우 NULL' --승리코드로 넣고 싶은데, 승리코드를 넣으려면 event-service에도 team_table 추가해야함.,
    created_at      datetime    NOT NULL    DEFAULT CURRENT_TIMESTAMP,
	updated_at	    datetime	NOT NULL    DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    UNIQUE KEY uq_result (match_date, start_time, away_team, home_team) -- 한 경기 유일성 
);


CREATE TABLE predict (
	idx	            bigint	    NOT NULL AUTO_INCREMENT PRIMARY KEY,
	result_id	    int	        NOT NULL,
	token_id	    int	        NOT NULL,
	match_date	    date	    NOT NULL,
	predicted	    varchar(10)	NOT NULL, -- 만약 보기가 '원정팀'. '홈팀'인 경우, predicted와 비교하는 코드가 필요함.
    created_at      datetime    NOT NULL    DEFAULT CURRENT_TIMESTAMP,
	updated_at	    datetime	NOT NULL    DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    CONSTRAINT fk_predict_result FOREIGN KEY  (result_id) REFERENCES result(idx) 
    ON DELETE RESTRICT ON UPDATE CASCADE,
    -- 1인당 특정일자에 1번만 참여 가능
    UNIQUE KEY uq_predict_once_per_day (token_id, match_date)
);


CREATE TABLE coupon (
	idx	            bigint	        NOT NULL AUTO_INCREMENT PRIMARY KEY,
    predict_id	    bigint	        NOT NULL,
	token_id	    int	            NOT NULL,
	code	        varchar(100)	NOT NULL,
	coupon_status	tinyint(1)	    NOT NULL	COMMENT '1 = 사용 or 만료 0 = 미사용',
    created_at      datetime        NOT NULL    DEFAULT CURRENT_TIMESTAMP,
	updated_at	    datetime	    NOT NULL    DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
	expire_at	    datetime	    NOT NULL,
    UNIQUE KEY uq_coupon_code (code), -- 쿠폰의 유일성
    UNIQUE KEY uq_coupon_predict (predict_id), -- 예측 1건당 쿠폰 1개
    KEY idx_coupon_token (token_id),
    CONSTRAINT fk_coupon_predict FOREIGN KEY (predict_id) REFERENCES predict(idx)
    ON DELETE CASCADE ON UPDATE CASCADE
	
);


CREATE TABLE total_rank (
	idx	    smallint	    NOT NULL AUTO_INCREMENT PRIMARY KEY,
	rank	smallint	    NULL	COMMENT '시즌 시작 전엔 NULL',
	team	varchar(5)	    NOT NULL,   -- 팀코드로 하려면, event-service에도 info.team_table 있어야함.
	games	smallint	    NOT NULL,
	win	    smallint	    NULL,
	lose	smallint	    NULL,
	rate	decimal(5,4)    NULL,
	gb	    decimal(4,1)	NULL	COMMENT 'games_behind',
	streak	varchar(5)	NULL
);

CREATE TABLE defend_rank (
	idx	                smallint	    NOT NULL AUTO_INCREMENT PRIMARY KEY,
	rank	            smallint	    NULL	COMMENT '시즌 시작 전엔 NULL',
	team	            varchar(5)	    NOT NULL,
	innings	            varchar(10)	    NULL,
	hits_allowed	    smallint	    NULL,
	home_runs_allowed	smallint	    NULL,
	runs_allowed	    smallint	    NULL,
	earned_runs	        smallint	    NULL,
	walks_hit_by_pitch	smallint	    NULL,
	strikeouts	        smallint	    NULL,
	era	                decimal(5,3)	NULL,
	errors	            smallint	    NULL,
	whip	            decimal(5,3)	NULL,
	qs	                decimal(5,3)	NULL,
	holds	            smallint	    NULL,
	saves	            smallint	    NULL
);


CREATE TABLE attack_rank (
	idx	                smallint	    NOT NULL AUTO_INCREMENT PRIMARY KEY,
	rank	            smallint	    NULL	COMMENT '시즌 시작 전엔 NULL',
	team	            varchar(5)	    NOT NULL,
	at_bats	            smallint	    NULL,
	hits	            smallint	    NULL,
	doubles	            smallint	    NULL,
	triples	            smallint	    NULL,
	home_runs	        smallint	    NULL,
	rbi	                smallint	    NULL	COMMENT 'runs_batted_in',
	runs_scored	        smallint	    NULL,
	stolen_bases	    smallint	    NULL,
	walks_hit_by_pitch	smallint	    NULL,
	strikeout	        smallint	    NULL,
	double_plays	    smallint	    NULL,
	batting_avg	        decimal(5,3)	NULL,
	obp	                decimal(5,3)	NULL	COMMENT 'on_base_pct',
	slg	                decimal(5,3)	NULL	COMMENT 'slugging_pct',
	ops	                decimal(5,3)	NULL
);



