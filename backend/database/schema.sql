-- CIVIL ENGINEERING MARKETPLACE DATABASE SCHEMA

-- 1. ENUMS
CREATE TYPE user_role AS ENUM ('user', 'worker', 'engineer', 'shopkeeper', 'admin');
CREATE TYPE registration_status AS ENUM ('pending', 'approved', 'rejected');
CREATE TYPE item_type AS ENUM ('sell', 'rent');
CREATE TYPE order_status AS ENUM ('pending', 'confirmed', 'shipped', 'delivered', 'cancelled');

-- 2. USERS TABLE
CREATE TABLE users (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    email TEXT UNIQUE NOT NULL,
    password_hash TEXT NOT NULL,
    user_type user_role NOT NULL,
    full_name TEXT,
    profile_pic_url TEXT,
    bio TEXT,
    age INTEGER,
    experience_years INTEGER DEFAULT 0,
    completed_projects INTEGER DEFAULT 0,
    address TEXT,
    location JSONB DEFAULT '{"lat": 0, "lng": 0, "address": ""}',
    is_active BOOLEAN DEFAULT true,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT timezone('utc'::text, now()) NOT NULL,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT timezone('utc'::text, now()) NOT NULL
);

-- 3. WORKER REGISTRATIONS
CREATE TABLE worker_registrations (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    user_id UUID REFERENCES users(id) ON DELETE CASCADE NOT NULL,
    name TEXT NOT NULL,
    phone TEXT NOT NULL,
    location JSONB NOT NULL, -- {lat, lng, address}
    work_type TEXT NOT NULL,
    daily_wages DECIMAL NOT NULL,
    aadhar_image_url TEXT,
    status registration_status DEFAULT 'pending',
    admin_notes TEXT,
    submitted_at TIMESTAMP WITH TIME ZONE DEFAULT now()
);

-- 4. ENGINEER REGISTRATIONS
CREATE TABLE engineer_registrations (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    user_id UUID REFERENCES users(id) ON DELETE CASCADE NOT NULL,
    name TEXT NOT NULL,
    phone TEXT NOT NULL,
    gmail TEXT,
    completion_cert_url TEXT,
    civil_eng_cert_url TEXT,
    aadhar_image_url TEXT,
    status registration_status DEFAULT 'pending',
    portfolio_photos JSONB DEFAULT '[]',
    pricing JSONB DEFAULT '{"hourly_rate": 0, "project_rate": 0}',
    admin_notes TEXT,
    submitted_at TIMESTAMP WITH TIME ZONE DEFAULT now()
);

-- 5. SHOPKEEPER REGISTRATIONS
CREATE TABLE shopkeeper_registrations (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    user_id UUID REFERENCES users(id) ON DELETE CASCADE NOT NULL,
    name TEXT NOT NULL,
    shop_name TEXT,
    phone TEXT NOT NULL,
    shop_photos JSONB DEFAULT '[]',
    gst_doc TEXT,
    shop_photo TEXT,
    gst_document_url TEXT,
    gst_number TEXT,
    aadhar_image_url TEXT,
    shop_location JSONB NOT NULL, -- {lat, lng, address}
    status registration_status DEFAULT 'pending',
    admin_notes TEXT,
    submitted_at TIMESTAMP WITH TIME ZONE DEFAULT now()
);

-- 5b. RENTER REGISTRATIONS
CREATE TABLE renter_registrations (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    user_id UUID REFERENCES users(id) ON DELETE CASCADE NOT NULL,
    name TEXT NOT NULL,
    phone TEXT NOT NULL,
    email TEXT,
    verification_doc_url TEXT,
    location JSONB, -- {lat, lng, manual_address}
    status registration_status DEFAULT 'pending',
    submitted_at TIMESTAMP WITH TIME ZONE DEFAULT now()
);

-- 6. ITEMS TABLE (Materials & Rental Equipment)
CREATE TABLE items (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    owner_id UUID REFERENCES users(id) ON DELETE CASCADE NOT NULL,
    name TEXT NOT NULL,
    description TEXT,
    category TEXT NOT NULL, -- e.g. 'Vehicle', 'Tools', 'Cement'
    image_url TEXT, -- Primary image
    extra_images JSONB DEFAULT '[]', -- Gallery
    price DECIMAL NOT NULL,
    item_type item_type NOT NULL, -- 'sell' or 'rent'
    price_unit TEXT DEFAULT 'piece', -- 'hour', 'day', 'piece'
    insurance_url TEXT, -- Required for Vehicle rentals
    location JSONB,
    stock INTEGER DEFAULT 1,
    is_active BOOLEAN DEFAULT true,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT now()
);

-- 7. ORDERS TABLE
CREATE TABLE orders (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    user_id UUID REFERENCES users(id) ON DELETE SET NULL,
    items JSONB NOT NULL, -- [{item_id, quantity, price}]
    total_amount DECIMAL NOT NULL,
    order_status order_status DEFAULT 'pending',
    delivery_location JSONB,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT now()
);

-- 8. ENGINEER PORTFOLIO
CREATE TABLE engineer_portfolio (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    engineer_id UUID REFERENCES users(id) ON DELETE CASCADE NOT NULL,
    project_name TEXT NOT NULL,
    description TEXT,
    images JSONB DEFAULT '[]',
    price_range TEXT,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT now()
);

-- 9. MESSAGES
CREATE TABLE messages (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    sender_id UUID REFERENCES users(id) ON DELETE CASCADE NOT NULL,
    recipient_id UUID REFERENCES users(id) ON DELETE CASCADE NOT NULL,
    message TEXT NOT NULL,
    is_read BOOLEAN DEFAULT false,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT now()
);

-- 10. GOVT SCHEMES
CREATE TABLE govt_schemes (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    title TEXT NOT NULL,
    description TEXT,
    eligibility TEXT,
    benefits TEXT,
    apply_link TEXT,
    source TEXT,
    last_updated TIMESTAMP WITH TIME ZONE DEFAULT now()
);

-- INDEXES
CREATE INDEX idx_users_email ON users(email);
CREATE INDEX idx_items_name_desc ON items USING gin(to_tsvector('english', name || ' ' || description));
CREATE INDEX idx_schemes_title_desc ON govt_schemes USING gin(to_tsvector('english', title || ' ' || description));

-- ROW LEVEL SECURITY (RLS)
-- Enable RLS on all tables
ALTER TABLE users ENABLE ROW LEVEL SECURITY;
ALTER TABLE worker_registrations ENABLE ROW LEVEL SECURITY;
ALTER TABLE engineer_registrations ENABLE ROW LEVEL SECURITY;
ALTER TABLE shopkeeper_registrations ENABLE ROW LEVEL SECURITY;
ALTER TABLE items ENABLE ROW LEVEL SECURITY;
ALTER TABLE orders ENABLE ROW LEVEL SECURITY;
ALTER TABLE engineer_portfolio ENABLE ROW LEVEL SECURITY;
ALTER TABLE messages ENABLE ROW LEVEL SECURITY;
ALTER TABLE govt_schemes ENABLE ROW LEVEL SECURITY;

-- POLICIES (Simplified for AI generation)
-- Users can read their own profiles
CREATE POLICY "Users can view own data" ON users FOR SELECT USING (auth.uid() = id);
-- Public can view approved schemes and items
CREATE POLICY "Public can view schemes" ON govt_schemes FOR SELECT USING (true);
CREATE POLICY "Public can view active items" ON items FOR SELECT USING (is_active = true);
-- Admin has bypass
-- Note: In Supabase, service_role key bypasses RLS. Admin logic goes here for SQL if needed.

-- STORAGE BUCKETS (CLI Commands representation)
-- Note: These are usually done via Supabase dashboard or API, but here are the SQL equivalents for RLS on buckets
-- Insert into storage.buckets (id, name, public) values ('documents', 'documents', true);
-- Insert into storage.buckets (id, name, public) values ('shop-photos', 'shop-photos', true);
-- Insert into storage.buckets (id, name, public) values ('portfolio', 'portfolio', true);
-- Engineer Projects (Portfolio)
CREATE TABLE IF NOT EXISTS engineer_projects (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    engineer_id UUID REFERENCES users(id),
    title TEXT NOT NULL,
    description TEXT,
    cost DECIMAL,
    location TEXT,
    duration_days INTEGER,
    sketch_url TEXT,
    images TEXT[],
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

-- Engineer Certifications
CREATE TABLE IF NOT EXISTS engineer_certifications (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    engineer_id UUID REFERENCES users(id),
    title TEXT NOT NULL,
    category TEXT, -- 'Engineer' or 'Material'
    image_url TEXT,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

-- Worker Attendance & Work Assignments
CREATE TABLE IF NOT EXISTS worker_management (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    engineer_id UUID REFERENCES users(id),
    worker_name TEXT NOT NULL,
    worker_code TEXT, -- Unique code assigned to worker
    location TEXT,
    assigned_work TEXT,
    attendance_status TEXT DEFAULT 'present', -- 'present', 'absent', 'on_leave'
    status TEXT DEFAULT 'assigned', -- 'assigned', 'accepted', 'rejected', 'started', 'completed'
    arrival_selfie_url TEXT,
    completion_photo_url TEXT,
    accepted_at TIMESTAMP WITH TIME ZONE,
    started_at TIMESTAMP WITH TIME ZONE,
    completed_at TIMESTAMP WITH TIME ZONE,
    date DATE DEFAULT CURRENT_DATE,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS govt_schemes (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    title TEXT NOT NULL,
    category TEXT,
    description TEXT,
    official_link TEXT,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);
