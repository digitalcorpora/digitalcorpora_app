create database search_tr;
create user 'dbreader'@'%' identified by random password;
create user 'dbwriter'@'%' identified by random password;
grant user 'dbreader'@'%' select on search_tr.*;
grant ALL on search_tr.* to 'dbwriter'@'%';
