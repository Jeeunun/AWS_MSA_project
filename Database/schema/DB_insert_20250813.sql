-- team_table
ALTER TABLE team ADD CONSTRAINT uq_team_code UNIQUE (code);

INSERT INTO team (t_name, code, city, stadium) VALUES 
    ('LG트윈스', 'LG', '서울특별시', '잠실야구장'),
    ('두산베어스', 'DS', '서울특별시', '잠실야구장'),
    ('키움히어로즈', 'KO', '서울특별시', '고척스카이돔'),
    ('SSG랜더스', 'SSG', '인천광역시', '인천SSG랜더스필드'),
    ('KT위즈', 'KT', '수원시(경기도)', '수원KT위즈파크'),
    ('삼성라이온즈', 'SS', '대구광역시', '대구삼성라이온즈파크'),
    ('롯데자이언츠', 'LT', '부산광역시', '사직야구장'),
    ('NC다이노스', 'NC', '창원시(경남)', '창원NC파크'),
    ('한화이글스', 'HH', '대전광역시', '대전한화생명이글스파크'),
    ('기아타이거즈', 'KIA', '광주광역시', '광주-기아챔피언스필드'),
    AS NEW
    ON DUPLICATE KEY UPDATE t_name=NEW.t_name, city=NEW.city, stadium=NEW.stadium;

