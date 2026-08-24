export interface Role {
  id: number
  name: string
  description: string
  permissions: string[]
  is_system: boolean
}
export interface User {
  id: number
  username: string
  full_name: string
  department: string
  is_active: boolean
  must_change_password: boolean
  role: Role
  created_at: string
}
export interface Material {
  id: number
  code: string
  name: string
  category_id: number | null
  location_id: number | null
  supplier_id: number | null
  mpn: string
  specification: string
  package: string
  footprint: string
  manufacturer: string
  unit: string
  unit_price: string
  safety_stock: string
  target_stock: string
  quantity: string
  reserved_quantity: string
  available_quantity: string
  barcode: string
  lifecycle_status: string
  rohs_status: string
  datasheet_url: string
  tags: string[]
  attributes: Record<string, unknown>
  notes: string
  is_active: boolean
  created_at: string
  updated_at: string
}
export interface Page<T> {
  items: T[]
  total: number
  page: number
  page_size: number
}
export type CableKind = 'terminal' | 'flat_flex' | 'micro_coax' | 'rf_coax'
export type CableEndStyle =
  'double' | 'single' | 'single_tinned' | 'male_female_pair' | 'unspecified'
export type CableDirection = 'same' | 'reverse' | 'unspecified'
export interface Cable {
  id: number
  code: string
  name: string
  custom_name: string
  model: string
  cable_kind: CableKind
  end_style: CableEndStyle
  connector_a: string
  connector_b: string
  connector_pitch_mm: string
  direction: CableDirection
  length_cm: string
  pin_count: number
  pin_count_b: number
  pin_layout: string
  quantity: number
  reserved_quantity: number
  available_quantity: number
  unit_price: string
  storage_location: string
  notes: string
  updated_at: string
}
export interface CablePage {
  items: Cable[]
  total: number
  page: number
  page_size: number
  summary: {
    quantity: number
    available_quantity: number
    in_stock_types: number
    pitch_count: number
  }
  facets: {
    connector_pitches: string[]
    lengths: string[]
    pin_counts: number[]
    cable_kinds: CableKind[]
    end_styles: CableEndStyle[]
  }
}
export interface CableImportSourceItem {
  key: string
  identity: string
  item_id: string
  variant: string
  quantity: number
  order_no: string
  source_row: number
  unit_price: string
  product_url: string
}
export interface CableImportRow {
  selected: boolean
  valid: boolean
  confidence: 'high' | 'medium' | 'low'
  source_rows: number[]
  source_line_count: number
  source_items: CableImportSourceItem[]
  name: string
  model: string
  cable_kind: CableKind
  end_style: CableEndStyle
  connector_a: string
  connector_b: string
  connector_pitch_mm: string | null
  direction: CableDirection
  length_cm: string
  pin_count: number
  pin_count_b: number
  pin_layout: string
  quantity: number
  unit_price: string
  storage_location: string
  notes: string
  shop: string
  status: string
  raw_product_name: string
  raw_variant: string
  warnings: string[]
  issues: string[]
  existing_cable_id: number | null
  existing_cable_code: string
  import_action: 'create' | 'increase' | 'skip'
}
export interface CableImportPreview {
  filename: string
  detected_format: string
  rows: CableImportRow[]
  summary: {
    source_rows: number
    recognized_rows: number
    spec_count: number
    merged_rows: number
    quantity: number
    valid_quantity: number
    shops: string[]
    existing_specs: number
    already_imported_specs: number
  }
}
export interface CableImportResult {
  created: number
  increased: number
  skipped: number
  imported_specs: number
  quantity_added: number
  cable_ids: number[]
  idempotent_replay?: boolean
}
export interface ApiError {
  code: string
  message: string
  details: Record<string, unknown>
  request_id: string
}
