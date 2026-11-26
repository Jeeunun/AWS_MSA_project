-- user-service
CREATE DATABASE IF NOT EXISTS user_service
    DEFAULT CHARACTER SET  utf8mb4
    DEFAULT COLLATE utf8mb4_unicode_ci;
USE user_service;

CREATE TABLE user (
    idx             BIGINT          NOT NULL AUTO_INCREMENT COMMENT '사용자 PK',
    cognito_sub     VARCHAR(20)     NOT NULL COMMENT '사용자 토큰',
    username        VARCHAR(20)     NULL COMMENT '실제 사용자 id',
    name            VARCHAR(10)     NOT NULL COMMENT '사용자 이름',
    password        VARCHAR(100)    NULL COMMENT '비밀번호',
    email           VARCHAR(20)     NULL COMMENT '이메일',
    tel             VARCHAR(20)     NULL COMMENT '전화번호',
    birth           DATE            NULL COMMENT '생년월일',
    team            VARCHAR(10)     NULL COMMENT '팀',
    date_joined     DATETIME        NOT NULL DEFAULT CURRENT_TIMESTAMP COMMENT '가입일',
    cognito_status  VARCHAR(20)     NOT NULL,
    PRIMARY KEY (idx)
) COMMENT='사용자';


-- board-service
CREATE DATABASE IF NOT EXISTS board_service
    DEFAULT CHARACTER SET  utf8mb4
    DEFAULT COLLATE utf8mb4_unicode_ci;
USE board_service;


CREATE TABLE post (
    idx             BIGINT          NOT NULL AUTO_INCREMENT COMMENT '게시글 PK',
    author          varchar(50)     NOT NULL COMMENT '사용자가 가입한 아이디',
    user_id         VARCHAR(128)    NOT NULL COMMENT 'cognito_sub값',
    category        VARCHAR(100)    NOT NULL COMMENT '카테고리',
    title           VARCHAR(100)    NOT NULL COMMENT '제목',
    content         TEXT            NOT NULL COMMENT '내용',
    views           INT             NOT NULL DEFAULT 0 COMMENT '조회수',
    created_at      DATETIME        NOT NULL DEFAULT CURRENT_TIMESTAMP COMMENT '작성일',
    updated_at      DATETIME        NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP COMMENT '수정일',
    is_pinned       TINYINT(1)      NOT NULL DEFAULT 0 COMMENT '고정여부',
    pin_category    VARCHAR(20)     NOT NULL COMMENT '고정행위',
    pin_type        VARCHAR(20)     NOT NULL COMMENT '고정타입',
    PRIMARY KEY (idx)
) COMMENT='게시글';

CREATE TABLE comment (
    idx         BIGINT      NOT NULL AUTO_INCREMENT COMMENT '댓글 PK',
    post_id     BIGINT      NOT NULL COMMENT '게시글 PK',
    user_id     INT         NOT NULL COMMENT '댓글작성자 id',
    content     TEXT        NOT NULL COMMENT '댓글내용',
    created_at  DATETIME    NOT NULL DEFAULT CURRENT_TIMESTAMP COMMENT '작성일',
    updated_at  DATETIME    NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP COMMENT '수정일',
    PRIMARY KEY (idx),
    FOREIGN KEY (post_id) REFERENCES post(idx) ON DELETE CASCADE ON UPDATE CASCADE
) COMMENT='댓글';


-- news-service
CREATE DATABASE IF NOT EXISTS news_service
    DEFAULT CHARACTER SET  utf8mb4
    DEFAULT COLLATE utf8mb4_unicode_ci;
USE news_service;

CREATE TABLE news (
    idx         BIGINT          NOT NULL AUTO_INCREMENT COMMENT '뉴스 PK',
    title       VARCHAR(200)    NOT NULL COMMENT '제목',
    keyword     VARCHAR(100)    NULL COMMENT '키워드',
    link        VARCHAR(1000)   NULL COMMENT '링크',
    crawl_date  DATE            NOT NULL COMMENT '크롤링한 날짜',
    created_at  DATETIME        NOT NULL DEFAULT CURRENT_TIMESTAMP COMMENT '생성일',
    PRIMARY KEY (idx),
    UNIQUE KEY uk_link (link)
) COMMENT='뉴스';


-- info-service
CREATE DATABASE IF NOT EXISTS info_service
    DEFAULT CHARACTER SET  utf8mb4
    DEFAULT COLLATE utf8mb4_unicode_ci;
USE info_service;

CREATE TABLE team (
    idx         TINYINT         NOT NULL AUTO_INCREMENT COMMENT '팀 PK',
    t_name      VARCHAR(10)     NOT NULL COMMENT '팀 이름',
    code        VARCHAR(10)     NOT NULL COMMENT '팀 코드',
    city        VARCHAR(10)     NULL COMMENT '연고지',
    stadium     VARCHAR(20)     NULL COMMENT '구장',
    PRIMARY KEY (idx),
    UNIQUE KEY uk_code (code)
) COMMENT='팀';

CREATE TABLE info (
    idx         BIGINT          NOT NULL AUTO_INCREMENT COMMENT '정보 PK',
    team_id     TINYINT         NOT NULL COMMENT '팀 id',
    p_name      VARCHAR(10)     NOT NULL COMMENT '선수이름',
    p_number    SMALLINT        NOT NULL COMMENT '선수 등번호',
    p_position  VARCHAR(5)      NOT NULL COMMENT '포지션',
    height_cm   CHAR(5)         NULL COMMENT '키',
    weight_kg   DECIMAL(5, 1)   NULL COMMENT '몸무게',
    birth       DATE            NOT NULL COMMENT '생년월일',
    p_info      VARCHAR(10)     NOT NULL COMMENT '투타정보',
    url         VARCHAR(200)    NOT NULL COMMENT 'S3 URL'
    created_at  DATETIME        NOT NULL DEFAULT CURRENT_TIMESTAMP COMMENT '생성일',
    updated_at  DATETIME        NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP COMMENT '수정일',
    PRIMARY KEY (idx),
    FOREIGN KEY (team_id) REFERENCES team(idx) ON DELETE CASCADE ON UPDATE CASCADE
) COMMENT='정보';

-- event-service
CREATE DATABASE IF NOT EXISTS event_service
    DEFAULT CHARACTER SET  utf8mb4
    DEFAULT COLLATE utf8mb4_unicode_ci;
USE event_service;

CREATE TABLE schedule (
    idx             BIGINT                          NOT NULL AUTO_INCREMENT COMMENT '경기결과 PK',
    match_date      DATE                            NOT NULL DEFAULT (CURDATE()) COMMENT '날짜',
    startTime       VARCHAR(5)                      NULL COMMENT '시작시간',
    awayTeamName    VARCHAR(10)                     NULL COMMENT '원정팀',
    awayResult      TINYINT                         NULL COMMENT '원정팀점수',
    homeTeamName    VARCHAR(10)                     NULL COMMENT '홈팀',
    homeResult      TINYINT                         NULL COMMENT '홈팀점수',
    gameStatus      ENUM('BEFORE','END','CANCEL')   NOT NULL DEFAULT 'BEFORE' COMMENT '상태',
    fieldname       VARCHAR(30)                     NULL COMMENT '구장',
    winner          ENUM('AWAY', 'HOME')            NULL COMMENT '승리', 
    created_at      DATETIME                        NOT NULL DEFAULT CURRENT_TIMESTAMP COMMENT '생성일',
    updated_at      DATETIME                        NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP COMMENT '수정일',
    PRIMARY KEY (idx)
) COMMENT='경기결과';

CREATE TABLE predict (
    idx         BIGINT          NOT NULL    AUTO_INCREMENT COMMENT '사용자 예측 PK',
    result_id   BIGINT          NOT NULL    COMMENT '경기결과 id',
    user_id     VARCHAR(20)     NOT NULL    COMMENT '사용자 id',
    predicted   VARCHAR(10)     NULL        COMMENT '예측 (AWAY, HOME)',
    created_at  DATETIME        NOT NULL DEFAULT CURRENT_TIMESTAMP COMMENT '생성일',
    updated_at  DATETIME        NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP COMMENT '수정일',
    PRIMARY KEY (idx),
    FOREIGN KEY (result_id) REFERENCES schedule(idx) ON DELETE CASCADE ON UPDATE CASCADE
) COMMENT='사용자 예측';

CREATE TABLE coupon (
    idx             BIGINT          NOT NULL AUTO_INCREMENT COMMENT '쿠폰 PK',
    predict_id      BIGINT          NOT NULL COMMENT '사용자 예측 id',
    coupon_code     VARCHAR(100)    NOT NULL COMMENT '쿠폰코드',
    coupon_status   TINYINT(1)      NOT NULL COMMENT '쿠폰상태 (0 미사용, 1 사용, 2 만료)',
    created_at      DATETIME        NOT NULL DEFAULT CURRENT_TIMESTAMP COMMENT '생성일',
    updated_at      DATETIME        NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP COMMENT '수정일',
    expire_at       DATETIME        NOT NULL COMMENT '만료일',
    PRIMARY KEY (idx),
    FOREIGN KEY (predict_id) REFERENCES predict(idx) ON DELETE CASCADE ON UPDATE CASCADE
) COMMENT='쿠폰';

CREATE TABLE season(
    idx         INT         NOT NULL AUTO_INCREMENT COMMENT '시즌 PK',
    season      SMALLINT    NOT NULL COMMENT '시즌',
    startDate   DATE        NOT NULL COMMENT '시즌개막일',
    endDate     DATE        NOT NULL COMMENT '시즌종료일'
)

CREATE TABLE total_rank (
    idx         SMALLINT        NOT NULL AUTO_INCREMENT COMMENT '종합순위 PK',
    season_id   INT             NOT NULL COMMENT '시즌 fk',
    rank        SMALLINT        NOT NULL DEFAULT 999 COMMENT '순위',
    team        VARCHAR(50)     NOT NULL COMMENT '팀',
    game        SMALLINT        NOT NULL COMMENT '경기',
    win         SMALLINT        NOT NULL COMMENT '승',
    draw        SMALLINT        NOT NULL COMMENT '무',
    loss        SMALLINT        NOT NULL COMMENT '패',
    wpct        DECIMAL(5, 4)   NOT NULL COMMENT '승률',
    gb          DECIMAL(4, 1)   NOT NULL COMMENT '게임차',
    streak      VARCHAR(5)      NULL COMMENT '연승',
    PRIMARY KEY (idx),
    FOREIGN KEY (season_id) REFERENCES season(idx) ON DELETE CASCADE ON UPDATE CASCADE
) COMMENT='종합순위';

CREATE TABLE attack_rank (
    idx         SMALLINT        NOT NULL AUTO_INCREMENT COMMENT '공격순위 PK',
    season_id   INT             NOT NULL COMMENT '시즌 fk',
    rank        SMALLINT        NOT NULL DEFAULT 999 COMMENT '순위',
    team        VARCHAR(5)      NOT NULL COMMENT '팀',
    batAB       SMALLINT        NOT NULL COMMENT '타수',
    batH        SMALLINT        NOT NULL COMMENT '안타',
    bat2b       SMALLINT        NOT NULL COMMENT '2루타',
    bat3b       SMALLINT        NOT NULL COMMENT '3루타',
    batHR       SMALLINT        NOT NULL COMMENT '홈런',
    batRBI      SMALLINT        NOT NULL COMMENT '타점',
    batR        SMALLINT        NOT NULL COMMENT '득점',
    batSB       SMALLINT        NOT NULL COMMENT '도루',
    batBbp      SMALLINT        NOT NULL COMMENT '사사구',
    batSo       SMALLINT        NOT NULL COMMENT '삼진',
    batGDp      SMALLINT        NOT NULL COMMENT '병살',
    batAvg      DECIMAL(5, 3)   NOT NULL COMMENT '타율',
    batOBp      DECIMAL(5, 3)   NOT NULL COMMENT '출루율',
    batSlg      DECIMAL(5, 3)   NOT NULL COMMENT '장타율',
    batOPs      DECIMAL(5, 3)   NOT NULL COMMENT 'OPS',
    PRIMARY KEY (idx),
    FOREIGN KEY (season_id) REFERENCES season(idx) ON DELETE CASCADE ON UPDATE CASCADE
) COMMENT='공격순위';

CREATE TABLE defense_rank (
    idx     SMALLINT        NOT NULL    AUTO_INCREMENT COMMENT '수비순위 PK',
    season_id   INT         NOT NULL COMMENT '시즌 fk',
    rank    SMALLINT        NOT NULL    COMMENT '순위',
    team    VARCHAR(5)      NOT NULL    COMMENT '팀',
    pitP    VARCHAR(10)     NULL        COMMENT '이닝',
    pitH    SMALLINT        NULL        COMMENT '피안타',
    pitHr   SMALLINT        NULL COMMENT '피홈런',
    pitR    SMALLINT        NULL COMMENT '실점',
    pitEr   SMALLINT        NULL COMMENT '자책',
    pitBbhp SMALLINT        NULL COMMENT '사사구',
    pitSo   SMALLINT        NULL COMMENT '탈삼진',
    pitEra  DECIMAL(5, 3)   NULL COMMENT '평균자책',
    fldErr  SMALLINT        NULL COMMENT '실책',
    whip    DECIMAL(5, 3)   NULL COMMENT 'whip',
    pitQs   DECIMAL(5, 3)   NULL COMMENT 'QS',
    pitHld  SMALLINT        NULL COMMENT '홀드',
    pitSv   SMALLINT        NULL COMMENT '세이브',
    PRIMARY KEY (idx),
    FOREIGN KEY (season_id) REFERENCES season(idx) ON DELETE CASCADE ON UPDATE CASCADE
) COMMENT='수비순위';
