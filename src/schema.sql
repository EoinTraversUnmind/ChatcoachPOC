--drop table public.sessions;
--drop table public.chat_logs;
--drop table public.feedback;

create table if not exists public.sessions (
	session_id VARCHAR(255) PRIMARY KEY, -- Generated on the frontend
	session_time TIMESTAMP NOT NULL default current_timestamp,
	session_lbl VARCHAR (255), -- User-inputted label for this session
  parameters_lbl VARCHAR(2555), -- ID for the parameters used (from gsheet)
	session_parameters json -- All of the parameters
);

CREATE TABLE if not exists public.chat_logs (
	message_id serial PRIMARY KEY,
	message_time TIMESTAMP NOT NULL default current_timestamp,
	session_id VARCHAR(255) NOT NULL,
  parameters_lbl VARCHAR(255), -- Duplicate, maybe not needed
	chat_step int not null, -- 1 for the first message in a session, etc.
	input text,  -- User says
	output text, -- Bot says
	extras json
);

create table if not exists public.feedback (
	feedback_id serial PRIMARY KEY,
	feedback_time TIMESTAMP NOT NULL default current_timestamp,
	session_id VARCHAR(255) NOT NULL,
	chat_step int not null, -- Step for the last message sent prior to the feedback
	rating int,
	feedback_text text,
	extras json
);
