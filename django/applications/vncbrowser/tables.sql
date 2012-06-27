SET statement_timeout = 0;
SET client_encoding = 'UTF8';
SET standard_conforming_strings = off;
SET check_function_bodies = false;
SET client_min_messages = warning;
SET escape_string_warning = off;
SET search_path = public, pg_catalog;
CREATE TYPE double3d AS (
	x double precision,
	y double precision,
	z double precision
);
CREATE TYPE integer3d AS (
	x integer,
	y integer,
	z integer
);
CREATE TYPE rgba AS (
	r real,
	g real,
	b real,
	a real
);
CREATE FUNCTION on_edit() RETURNS trigger
    LANGUAGE plpgsql
    AS $$BEGIN
    NEW."edition_time" := now();
    RETURN NEW;
END;
$$;
SET default_with_oids = false;
CREATE TABLE applied_migrations (
    id character varying(32) NOT NULL
);
CREATE SEQUENCE broken_slice_id_seq
    START WITH 1
    INCREMENT BY 1
    NO MAXVALUE
    NO MINVALUE
    CACHE 1;
CREATE TABLE broken_slice (
    stack_id integer NOT NULL,
    index integer NOT NULL,
    id integer DEFAULT nextval('broken_slice_id_seq'::regclass) NOT NULL
);
CREATE TABLE concept (
    id bigint NOT NULL,
    user_id bigint NOT NULL,
    creation_time timestamp with time zone DEFAULT now() NOT NULL,
    edition_time timestamp with time zone DEFAULT now() NOT NULL,
    project_id bigint NOT NULL
);
CREATE TABLE class (
    class_name character varying(255) NOT NULL,
    description text
)
INHERITS (concept);
CREATE TABLE relation_instance (
    relation_id bigint NOT NULL
)
INHERITS (concept);
COMMENT ON TABLE relation_instance IS 'despite the table names, it is an abstract table only used for inheritance';
CREATE TABLE class_class (
    class_a bigint,
    class_b bigint
)
INHERITS (relation_instance);
COMMENT ON TABLE class_class IS 'relates two classes';
CREATE TABLE class_instance (
    class_id bigint NOT NULL,
    name character varying(255) NOT NULL
)
INHERITS (concept);
CREATE TABLE class_instance_class_instance (
    class_instance_a bigint,
    class_instance_b bigint
)
INHERITS (relation_instance);
COMMENT ON TABLE class_instance_class_instance IS 'relates two class_instances';
CREATE SEQUENCE concept_id_seq
    START WITH 1
    INCREMENT BY 1
    NO MAXVALUE
    NO MINVALUE
    CACHE 1;
ALTER SEQUENCE concept_id_seq OWNED BY concept.id;
CREATE TABLE location (
    location double3d NOT NULL,
    reviewer_id integer DEFAULT (-1) NOT NULL,
    review_time timestamp with time zone
)
INHERITS (concept);
CREATE TABLE connector (
    confidence integer DEFAULT 5 NOT NULL
)
INHERITS (location);
CREATE TABLE connector_class_instance (
    connector_id bigint NOT NULL,
    class_instance_id bigint NOT NULL
)
INHERITS (relation_instance);
CREATE TABLE log (
    operation_type character varying(255) NOT NULL,
    location double3d,
    freetext text
)
INHERITS (concept);
CREATE TABLE message (
    id integer NOT NULL,
    user_id integer NOT NULL,
    "time" timestamp with time zone DEFAULT now() NOT NULL,
    read boolean DEFAULT false NOT NULL,
    title text DEFAULT 'New message'::text NOT NULL,
    text text,
    action text
);
COMMENT ON COLUMN message.action IS 'URL to be executed (remember that this is not safe against man in the middle when not encrypted)';
CREATE SEQUENCE message_id_seq
    START WITH 1
    INCREMENT BY 1
    NO MAXVALUE
    NO MINVALUE
    CACHE 1;
ALTER SEQUENCE message_id_seq OWNED BY message.id;
CREATE TABLE "overlay" (
    id integer NOT NULL,
    stack_id integer NOT NULL,
    title text NOT NULL,
    image_base text NOT NULL,
    default_opacity integer DEFAULT 0 NOT NULL,
    file_extension text NOT NULL
);
CREATE SEQUENCE overlay_id_seq
    START WITH 1
    INCREMENT BY 1
    NO MAXVALUE
    NO MINVALUE
    CACHE 1;
ALTER SEQUENCE overlay_id_seq OWNED BY "overlay".id;
CREATE TABLE project (
    id integer NOT NULL,
    title text NOT NULL,
    public boolean DEFAULT true NOT NULL,
    wiki_base_url text
);
CREATE SEQUENCE project_id_seq
    START WITH 1
    INCREMENT BY 1
    NO MAXVALUE
    NO MINVALUE
    CACHE 1;
ALTER SEQUENCE project_id_seq OWNED BY project.id;
CREATE SEQUENCE project_stack_id_seq
    START WITH 1
    INCREMENT BY 1
    NO MAXVALUE
    NO MINVALUE
    CACHE 1;
CREATE TABLE project_stack (
    project_id integer NOT NULL,
    stack_id integer NOT NULL,
    translation double3d DEFAULT ROW((0)::double precision, (0)::double precision, (0)::double precision) NOT NULL,
    id integer DEFAULT nextval('project_stack_id_seq'::regclass) NOT NULL
);
COMMENT ON COLUMN project_stack.translation IS 'nanometer';
CREATE TABLE project_user (
    project_id integer NOT NULL,
    user_id integer NOT NULL,
    can_edit_any boolean DEFAULT false,
    can_view_any boolean DEFAULT false,
    inverse_mouse_wheel boolean DEFAULT false
);
CREATE TABLE relation (
    relation_name character varying(255) NOT NULL,
    uri text,
    description text,
    isreciprocal boolean DEFAULT false NOT NULL
)
INHERITS (concept);
COMMENT ON COLUMN relation.isreciprocal IS 'Is the converse of the relationship valid?';
CREATE TABLE sessions (
    id integer NOT NULL,
    session_id character(26),
    data text DEFAULT ''::text,
    last_accessed timestamp without time zone
);
CREATE SEQUENCE sessions_id_seq
    START WITH 1
    INCREMENT BY 1
    NO MAXVALUE
    NO MINVALUE
    CACHE 1;
ALTER SEQUENCE sessions_id_seq OWNED BY sessions.id;
CREATE TABLE settings (
    key text NOT NULL,
    value text
);
CREATE TABLE stack (
    id integer NOT NULL,
    title text NOT NULL,
    dimension integer3d NOT NULL,
    resolution double3d NOT NULL,
    image_base text NOT NULL,
    comment text,
    trakem2_project boolean DEFAULT false NOT NULL,
    num_zoom_levels integer DEFAULT (-1) NOT NULL,
    file_extension text DEFAULT 'jpg'::text NOT NULL,
    tile_width integer DEFAULT 256 NOT NULL,
    tile_height integer DEFAULT 256 NOT NULL,
    tile_source_type integer DEFAULT 1 NOT NULL,
    metadata text DEFAULT ''::text NOT NULL
);
COMMENT ON COLUMN stack.dimension IS 'pixel';
COMMENT ON COLUMN stack.resolution IS 'nanometer per pixel';
COMMENT ON COLUMN stack.image_base IS 'base URL to the images';
COMMENT ON COLUMN stack.trakem2_project IS 'States if a TrakEM2 project file is available for this stack.';
CREATE SEQUENCE stack_id_seq
    START WITH 1
    INCREMENT BY 1
    NO MAXVALUE
    NO MINVALUE
    CACHE 1;
ALTER SEQUENCE stack_id_seq OWNED BY stack.id;
CREATE TABLE textlabel (
    id integer NOT NULL,
    type character varying(32) NOT NULL,
    text text DEFAULT 'Edit this text ...'::text NOT NULL,
    colour rgba DEFAULT ROW((1)::real, (0.5)::real, (0)::real, (1)::real) NOT NULL,
    font_name text,
    font_style text,
    font_size double precision DEFAULT 32 NOT NULL,
    project_id integer NOT NULL,
    scaling boolean DEFAULT true NOT NULL,
    creation_time timestamp with time zone DEFAULT now() NOT NULL,
    edition_time timestamp with time zone DEFAULT now() NOT NULL,
    deleted boolean DEFAULT false NOT NULL,
    CONSTRAINT textlabel_type_check CHECK ((((type)::text = 'text'::text) OR ((type)::text = 'bubble'::text)))
);
CREATE SEQUENCE textlabel_id_seq
    START WITH 1
    INCREMENT BY 1
    NO MAXVALUE
    NO MINVALUE
    CACHE 1;
ALTER SEQUENCE textlabel_id_seq OWNED BY textlabel.id;
CREATE TABLE textlabel_location (
    textlabel_id integer NOT NULL,
    location double3d NOT NULL,
    deleted boolean DEFAULT false NOT NULL
);
CREATE TABLE treenode (
    parent_id bigint,
    radius double precision DEFAULT 0 NOT NULL,
    confidence integer DEFAULT 5 NOT NULL,
    skeleton_id bigint
)
INHERITS (location);
CREATE TABLE treenode_class_instance (
    treenode_id bigint NOT NULL,
    class_instance_id bigint NOT NULL
)
INHERITS (relation_instance);
CREATE TABLE treenode_connector (
    treenode_id bigint NOT NULL,
    connector_id bigint NOT NULL,
    skeleton_id bigint,
    confidence integer DEFAULT 5 NOT NULL
)
INHERITS (relation_instance);
CREATE TABLE "user" (
    id integer NOT NULL,
    name character varying(255) NOT NULL,
    pwd character varying(255) NOT NULL,
    longname text
);
CREATE SEQUENCE user_id_seq
    START WITH 1
    INCREMENT BY 1
    NO MAXVALUE
    NO MINVALUE
    CACHE 1;
ALTER SEQUENCE user_id_seq OWNED BY "user".id;
ALTER TABLE ONLY class ALTER COLUMN creation_time SET DEFAULT now();
ALTER TABLE ONLY class ALTER COLUMN edition_time SET DEFAULT now();
ALTER TABLE ONLY class ALTER COLUMN id SET DEFAULT nextval('concept_id_seq'::regclass);
ALTER TABLE ONLY class_class ALTER COLUMN creation_time SET DEFAULT now();
ALTER TABLE ONLY class_class ALTER COLUMN edition_time SET DEFAULT now();
ALTER TABLE ONLY class_class ALTER COLUMN id SET DEFAULT nextval('concept_id_seq'::regclass);
ALTER TABLE ONLY class_instance ALTER COLUMN creation_time SET DEFAULT now();
ALTER TABLE ONLY class_instance ALTER COLUMN edition_time SET DEFAULT now();
ALTER TABLE ONLY class_instance ALTER COLUMN id SET DEFAULT nextval('concept_id_seq'::regclass);
ALTER TABLE ONLY class_instance_class_instance ALTER COLUMN creation_time SET DEFAULT now();
ALTER TABLE ONLY class_instance_class_instance ALTER COLUMN edition_time SET DEFAULT now();
ALTER TABLE ONLY class_instance_class_instance ALTER COLUMN id SET DEFAULT nextval('concept_id_seq'::regclass);
ALTER TABLE ONLY concept ALTER COLUMN id SET DEFAULT nextval('concept_id_seq'::regclass);
ALTER TABLE ONLY connector ALTER COLUMN creation_time SET DEFAULT now();
ALTER TABLE ONLY connector ALTER COLUMN edition_time SET DEFAULT now();
ALTER TABLE ONLY connector ALTER COLUMN id SET DEFAULT nextval('concept_id_seq'::regclass);
ALTER TABLE ONLY connector ALTER COLUMN reviewer_id SET DEFAULT (-1);
ALTER TABLE ONLY connector_class_instance ALTER COLUMN creation_time SET DEFAULT now();
ALTER TABLE ONLY connector_class_instance ALTER COLUMN edition_time SET DEFAULT now();
ALTER TABLE ONLY connector_class_instance ALTER COLUMN id SET DEFAULT nextval('concept_id_seq'::regclass);
ALTER TABLE ONLY location ALTER COLUMN creation_time SET DEFAULT now();
ALTER TABLE ONLY location ALTER COLUMN edition_time SET DEFAULT now();
ALTER TABLE ONLY location ALTER COLUMN id SET DEFAULT nextval('concept_id_seq'::regclass);
ALTER TABLE ONLY log ALTER COLUMN id SET DEFAULT nextval('concept_id_seq'::regclass);
ALTER TABLE ONLY log ALTER COLUMN creation_time SET DEFAULT now();
ALTER TABLE ONLY log ALTER COLUMN edition_time SET DEFAULT now();
ALTER TABLE ONLY message ALTER COLUMN id SET DEFAULT nextval('message_id_seq'::regclass);
ALTER TABLE ONLY "overlay" ALTER COLUMN id SET DEFAULT nextval('overlay_id_seq'::regclass);
ALTER TABLE ONLY project ALTER COLUMN id SET DEFAULT nextval('project_id_seq'::regclass);
ALTER TABLE ONLY relation ALTER COLUMN creation_time SET DEFAULT now();
ALTER TABLE ONLY relation ALTER COLUMN edition_time SET DEFAULT now();
ALTER TABLE ONLY relation ALTER COLUMN id SET DEFAULT nextval('concept_id_seq'::regclass);
ALTER TABLE ONLY relation_instance ALTER COLUMN creation_time SET DEFAULT now();
ALTER TABLE ONLY relation_instance ALTER COLUMN edition_time SET DEFAULT now();
ALTER TABLE ONLY relation_instance ALTER COLUMN id SET DEFAULT nextval('concept_id_seq'::regclass);
ALTER TABLE ONLY sessions ALTER COLUMN id SET DEFAULT nextval('sessions_id_seq'::regclass);
ALTER TABLE ONLY stack ALTER COLUMN id SET DEFAULT nextval('stack_id_seq'::regclass);
ALTER TABLE ONLY textlabel ALTER COLUMN id SET DEFAULT nextval('textlabel_id_seq'::regclass);
ALTER TABLE ONLY treenode ALTER COLUMN creation_time SET DEFAULT now();
ALTER TABLE ONLY treenode ALTER COLUMN edition_time SET DEFAULT now();
ALTER TABLE ONLY treenode ALTER COLUMN id SET DEFAULT nextval('concept_id_seq'::regclass);
ALTER TABLE ONLY treenode ALTER COLUMN reviewer_id SET DEFAULT (-1);
ALTER TABLE ONLY treenode_class_instance ALTER COLUMN creation_time SET DEFAULT now();
ALTER TABLE ONLY treenode_class_instance ALTER COLUMN edition_time SET DEFAULT now();
ALTER TABLE ONLY treenode_class_instance ALTER COLUMN id SET DEFAULT nextval('concept_id_seq'::regclass);
ALTER TABLE ONLY treenode_connector ALTER COLUMN creation_time SET DEFAULT now();
ALTER TABLE ONLY treenode_connector ALTER COLUMN edition_time SET DEFAULT now();
ALTER TABLE ONLY treenode_connector ALTER COLUMN id SET DEFAULT nextval('concept_id_seq'::regclass);
ALTER TABLE ONLY "user" ALTER COLUMN id SET DEFAULT nextval('user_id_seq'::regclass);
ALTER TABLE ONLY applied_migrations
    ADD CONSTRAINT applied_migrations_pkey PRIMARY KEY (id);
ALTER TABLE ONLY broken_slice
    ADD CONSTRAINT broken_slice_pkey PRIMARY KEY (id);
ALTER TABLE ONLY class
    ADD CONSTRAINT class_id_key UNIQUE (id);
ALTER TABLE ONLY class_instance
    ADD CONSTRAINT class_instance_id_key UNIQUE (id);
ALTER TABLE ONLY class_instance
    ADD CONSTRAINT class_instance_pkey PRIMARY KEY (id);
ALTER TABLE ONLY class_instance_class_instance
    ADD CONSTRAINT class_instance_relation_instance_id_key UNIQUE (id);
ALTER TABLE ONLY class_instance_class_instance
    ADD CONSTRAINT class_instance_relation_instance_pkey PRIMARY KEY (id);
ALTER TABLE ONLY class
    ADD CONSTRAINT class_pkey PRIMARY KEY (id);
ALTER TABLE ONLY class_class
    ADD CONSTRAINT class_relation_instance_id_key UNIQUE (id);
ALTER TABLE ONLY class_class
    ADD CONSTRAINT class_relation_instance_pkey PRIMARY KEY (id);
ALTER TABLE ONLY concept
    ADD CONSTRAINT concept_id_key UNIQUE (id);
ALTER TABLE ONLY concept
    ADD CONSTRAINT concept_pkey PRIMARY KEY (id);
ALTER TABLE ONLY connector_class_instance
    ADD CONSTRAINT connector_class_instance_id_key UNIQUE (id);
ALTER TABLE ONLY connector_class_instance
    ADD CONSTRAINT connector_class_instance_pkey PRIMARY KEY (id);
ALTER TABLE ONLY connector
    ADD CONSTRAINT connector_id_key UNIQUE (id);
ALTER TABLE ONLY connector
    ADD CONSTRAINT connector_pkey PRIMARY KEY (id);
ALTER TABLE ONLY location
    ADD CONSTRAINT location_id_key UNIQUE (id);
ALTER TABLE ONLY location
    ADD CONSTRAINT location_pkey PRIMARY KEY (id);
ALTER TABLE ONLY log
    ADD CONSTRAINT log_pkey PRIMARY KEY (id);
ALTER TABLE ONLY message
    ADD CONSTRAINT message_pkey PRIMARY KEY (id);
ALTER TABLE ONLY "overlay"
    ADD CONSTRAINT overlay_pkey PRIMARY KEY (id);
ALTER TABLE ONLY project
    ADD CONSTRAINT project_pkey PRIMARY KEY (id);
ALTER TABLE ONLY project_stack
    ADD CONSTRAINT project_stack_pkey PRIMARY KEY (id);
ALTER TABLE ONLY project_user
    ADD CONSTRAINT project_user_pkey PRIMARY KEY (project_id, user_id);
ALTER TABLE ONLY relation
    ADD CONSTRAINT relation_id_key UNIQUE (id);
ALTER TABLE ONLY relation_instance
    ADD CONSTRAINT relation_instance_id_key UNIQUE (id);
ALTER TABLE ONLY relation_instance
    ADD CONSTRAINT relation_instance_pkey PRIMARY KEY (id);
ALTER TABLE ONLY relation
    ADD CONSTRAINT relation_pkey PRIMARY KEY (id);
ALTER TABLE ONLY sessions
    ADD CONSTRAINT sessions_pkey PRIMARY KEY (id);
ALTER TABLE ONLY settings
    ADD CONSTRAINT settings_pkey PRIMARY KEY (key);
ALTER TABLE ONLY stack
    ADD CONSTRAINT stack_pkey PRIMARY KEY (id);
ALTER TABLE ONLY textlabel
    ADD CONSTRAINT textlabel_pkey PRIMARY KEY (id);
ALTER TABLE ONLY treenode_class_instance
    ADD CONSTRAINT treenode_class_instance_id_key UNIQUE (id);
ALTER TABLE ONLY treenode_class_instance
    ADD CONSTRAINT treenode_class_instance_pkey PRIMARY KEY (id);
ALTER TABLE ONLY treenode
    ADD CONSTRAINT treenode_id_key UNIQUE (id);
ALTER TABLE ONLY treenode
    ADD CONSTRAINT treenode_pkey PRIMARY KEY (id);
ALTER TABLE ONLY "user"
    ADD CONSTRAINT users_name_key UNIQUE (name);
ALTER TABLE ONLY "user"
    ADD CONSTRAINT users_pkey PRIMARY KEY (id);
CREATE INDEX connector_x_index ON connector USING btree (((location).x));
CREATE INDEX connector_y_index ON connector USING btree (((location).y));
CREATE INDEX connector_z_index ON connector USING btree (((location).z));
CREATE INDEX location_x_index ON treenode USING btree (((location).x));
CREATE INDEX location_y_index ON treenode USING btree (((location).y));
CREATE INDEX location_z_index ON treenode USING btree (((location).z));
CREATE TRIGGER apply_edition_time_update
    BEFORE UPDATE ON class_instance
    FOR EACH ROW
    EXECUTE PROCEDURE on_edit();
CREATE TRIGGER on_edit
    BEFORE UPDATE ON textlabel
    FOR EACH ROW
    EXECUTE PROCEDURE on_edit();
CREATE TRIGGER on_edit
    BEFORE UPDATE ON concept
    FOR EACH ROW
    EXECUTE PROCEDURE on_edit();
CREATE TRIGGER on_edit_class
    BEFORE UPDATE ON class
    FOR EACH ROW
    EXECUTE PROCEDURE on_edit();
CREATE TRIGGER on_edit_class_class
    BEFORE UPDATE ON class_class
    FOR EACH ROW
    EXECUTE PROCEDURE on_edit();
CREATE TRIGGER on_edit_class_instance
    BEFORE UPDATE ON class_instance
    FOR EACH ROW
    EXECUTE PROCEDURE on_edit();
CREATE TRIGGER on_edit_class_instance_class_instance
    BEFORE UPDATE ON class_instance_class_instance
    FOR EACH ROW
    EXECUTE PROCEDURE on_edit();
CREATE TRIGGER on_edit_connector
    BEFORE UPDATE ON connector
    FOR EACH ROW
    EXECUTE PROCEDURE on_edit();
CREATE TRIGGER on_edit_connector_class_instance
    BEFORE UPDATE ON connector_class_instance
    FOR EACH ROW
    EXECUTE PROCEDURE on_edit();
CREATE TRIGGER on_edit_location
    BEFORE UPDATE ON location
    FOR EACH ROW
    EXECUTE PROCEDURE on_edit();
CREATE TRIGGER on_edit_relation
    BEFORE UPDATE ON relation
    FOR EACH ROW
    EXECUTE PROCEDURE on_edit();
CREATE TRIGGER on_edit_relation_instance
    BEFORE UPDATE ON relation_instance
    FOR EACH ROW
    EXECUTE PROCEDURE on_edit();
CREATE TRIGGER on_edit_treenode
    BEFORE UPDATE ON treenode
    FOR EACH ROW
    EXECUTE PROCEDURE on_edit();
CREATE TRIGGER on_edit_treenode_class_instance
    BEFORE UPDATE ON treenode_class_instance
    FOR EACH ROW
    EXECUTE PROCEDURE on_edit();
CREATE TRIGGER on_edit_treenode_connector
    BEFORE UPDATE ON treenode_connector
    FOR EACH ROW
    EXECUTE PROCEDURE on_edit();
ALTER TABLE ONLY class_class
    ADD CONSTRAINT class_class_class_a_fkey FOREIGN KEY (class_a) REFERENCES class(id) ON DELETE CASCADE;
ALTER TABLE ONLY class_class
    ADD CONSTRAINT class_class_class_b_fkey FOREIGN KEY (class_b) REFERENCES class(id) ON DELETE CASCADE;
ALTER TABLE ONLY class_instance
    ADD CONSTRAINT class_instance_class_id_fkey FOREIGN KEY (class_id) REFERENCES class(id);
ALTER TABLE ONLY class_instance_class_instance
    ADD CONSTRAINT class_instance_class_instance_class_instance_a_fkey FOREIGN KEY (class_instance_a) REFERENCES class_instance(id) ON DELETE CASCADE;
ALTER TABLE ONLY class_instance_class_instance
    ADD CONSTRAINT class_instance_class_instance_class_instance_b_fkey FOREIGN KEY (class_instance_b) REFERENCES class_instance(id) ON DELETE CASCADE;
ALTER TABLE ONLY class_instance_class_instance
    ADD CONSTRAINT class_instance_relation_instance_relation_id_fkey FOREIGN KEY (relation_id) REFERENCES relation(id);
ALTER TABLE ONLY class_instance_class_instance
    ADD CONSTRAINT class_instance_relation_instance_user_id_fkey FOREIGN KEY (user_id) REFERENCES "user"(id);
ALTER TABLE ONLY class_instance
    ADD CONSTRAINT class_instance_user_id_fkey FOREIGN KEY (user_id) REFERENCES "user"(id);
ALTER TABLE ONLY class_class
    ADD CONSTRAINT class_relation_instance_relation_id_fkey FOREIGN KEY (relation_id) REFERENCES relation(id);
ALTER TABLE ONLY class_class
    ADD CONSTRAINT class_relation_instance_user_id_fkey FOREIGN KEY (user_id) REFERENCES "user"(id);
ALTER TABLE ONLY class
    ADD CONSTRAINT class_user_id_fkey FOREIGN KEY (user_id) REFERENCES "user"(id);
ALTER TABLE ONLY concept
    ADD CONSTRAINT concept_user_id_fkey FOREIGN KEY (user_id) REFERENCES "user"(id);
ALTER TABLE ONLY connector_class_instance
    ADD CONSTRAINT connector_class_instance_class_instance_id_fkey FOREIGN KEY (class_instance_id) REFERENCES class_instance(id) ON DELETE CASCADE;
ALTER TABLE ONLY connector_class_instance
    ADD CONSTRAINT connector_class_instance_location_id_fkey FOREIGN KEY (connector_id) REFERENCES connector(id) ON DELETE CASCADE;
ALTER TABLE ONLY connector_class_instance
    ADD CONSTRAINT connector_class_instance_project_id_fkey FOREIGN KEY (project_id) REFERENCES project(id);
ALTER TABLE ONLY connector_class_instance
    ADD CONSTRAINT connector_class_instance_relation_id_fkey FOREIGN KEY (relation_id) REFERENCES relation(id);
ALTER TABLE ONLY connector_class_instance
    ADD CONSTRAINT connector_class_instance_user_id_fkey FOREIGN KEY (user_id) REFERENCES "user"(id);
ALTER TABLE ONLY message
    ADD CONSTRAINT message_user_id_fkey FOREIGN KEY (user_id) REFERENCES "user"(id);
ALTER TABLE ONLY "overlay"
    ADD CONSTRAINT overlay_stack_id_fkey FOREIGN KEY (stack_id) REFERENCES stack(id) ON DELETE CASCADE;
ALTER TABLE ONLY project_stack
    ADD CONSTRAINT project_stack_project_id_fkey FOREIGN KEY (project_id) REFERENCES project(id);
ALTER TABLE ONLY project_stack
    ADD CONSTRAINT project_stack_stack_id_fkey FOREIGN KEY (stack_id) REFERENCES stack(id);
ALTER TABLE ONLY project_user
    ADD CONSTRAINT project_user_project_id_fkey FOREIGN KEY (project_id) REFERENCES project(id);
ALTER TABLE ONLY project_user
    ADD CONSTRAINT project_user_user_id_fkey FOREIGN KEY (user_id) REFERENCES "user"(id);
ALTER TABLE ONLY relation_instance
    ADD CONSTRAINT relation_instance_user_id_fkey FOREIGN KEY (user_id) REFERENCES "user"(id);
ALTER TABLE ONLY relation
    ADD CONSTRAINT relation_user_id_fkey FOREIGN KEY (user_id) REFERENCES "user"(id);
ALTER TABLE ONLY textlabel_location
    ADD CONSTRAINT textlabel_location_textlabel_id_fkey FOREIGN KEY (textlabel_id) REFERENCES textlabel(id);
ALTER TABLE ONLY textlabel
    ADD CONSTRAINT textlabel_project_id_fkey FOREIGN KEY (project_id) REFERENCES project(id);
ALTER TABLE ONLY treenode_class_instance
    ADD CONSTRAINT treenode_class_instance_class_instance_id_fkey FOREIGN KEY (class_instance_id) REFERENCES class_instance(id) ON DELETE CASCADE;
ALTER TABLE ONLY treenode_class_instance
    ADD CONSTRAINT treenode_class_instance_relation_id_fkey FOREIGN KEY (relation_id) REFERENCES relation(id);
ALTER TABLE ONLY treenode_class_instance
    ADD CONSTRAINT treenode_class_instance_treenode_id_fkey FOREIGN KEY (treenode_id) REFERENCES treenode(id) ON DELETE CASCADE;
ALTER TABLE ONLY treenode_class_instance
    ADD CONSTRAINT treenode_class_instance_user_id_fkey FOREIGN KEY (user_id) REFERENCES "user"(id);
ALTER TABLE ONLY treenode_connector
    ADD CONSTRAINT treenode_connector_connector_id_fkey FOREIGN KEY (connector_id) REFERENCES connector(id) ON DELETE CASCADE;
ALTER TABLE ONLY treenode_connector
    ADD CONSTRAINT treenode_connector_skeleton_id_fkey FOREIGN KEY (skeleton_id) REFERENCES class_instance(id) ON DELETE CASCADE;
ALTER TABLE ONLY treenode_connector
    ADD CONSTRAINT treenode_connector_treenode_id_fkey FOREIGN KEY (treenode_id) REFERENCES treenode(id) ON DELETE CASCADE;
ALTER TABLE ONLY treenode_connector
    ADD CONSTRAINT treenode_connector_user_id_fkey FOREIGN KEY (user_id) REFERENCES "user"(id);
ALTER TABLE ONLY treenode
    ADD CONSTRAINT treenode_parent_id_fkey FOREIGN KEY (parent_id) REFERENCES treenode(id);
ALTER TABLE ONLY treenode
    ADD CONSTRAINT treenode_skeleton_id_fkey FOREIGN KEY (skeleton_id) REFERENCES class_instance(id) ON DELETE CASCADE;
