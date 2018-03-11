DROP TABLE IF EXISTS  user ;
CREATE TABLE  user  (
   id  integer primary key autoincrement,
   username  text not null,
   password  text not null
);
