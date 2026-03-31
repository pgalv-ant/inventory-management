from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from typing import List, Optional
from pydantic import BaseModel
from mock_data import inventory_items, orders, demand_forecasts, backlog_items, spending_summary, monthly_spending, category_spending, recent_transactions, purchase_orders

app = FastAPI(title="Factory Inventory Management System")

# Quarter mapping for date filtering
QUARTER_MAP = {
    'Q1-2025': ['2025-01', '2025-02', '2025-03'],
    'Q2-2025': ['2025-04', '2025-05', '2025-06'],
    'Q3-2025': ['2025-07', '2025-08', '2025-09'],
    'Q4-2025': ['2025-10', '2025-11', '2025-12']
}

def filter_by_month(items: list, month: Optional[str]) -> list:
    """Filter items by month/quarter based on order_date field"""
    if not month or month == 'all':
        return items

    if month.startswith('Q'):
        # Handle quarters
        if month in QUARTER_MAP:
            months = QUARTER_MAP[month]
            return [item for item in items if any(m in item.get('order_date', '') for m in months)]
    else:
        # Direct month match
        return [item for item in items if month in item.get('order_date', '')]

    return items

def apply_filters(items: list, warehouse: Optional[str] = None, category: Optional[str] = None,
                 status: Optional[str] = None) -> list:
    """Apply common filters to a list of items"""
    filtered = items

    if warehouse and warehouse != 'all':
        filtered = [item for item in filtered if item.get('warehouse') == warehouse]

    if category and category != 'all':
        filtered = [item for item in filtered if item.get('category', '').lower() == category.lower()]

    if status and status != 'all':
        filtered = [item for item in filtered if item.get('status', '').lower() == status.lower()]

    return filtered

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Data models
class InventoryItem(BaseModel):
    id: str
    sku: str
    name: str
    category: str
    warehouse: str
    quantity_on_hand: int
    reorder_point: int
    unit_cost: float
    location: str
    last_updated: str

class Order(BaseModel):
    id: str
    order_number: str
    customer: str
    items: List[dict]
    status: str
    order_date: str
    expected_delivery: str
    total_value: float
    actual_delivery: Optional[str] = None
    warehouse: Optional[str] = None
    category: Optional[str] = None

class DemandForecast(BaseModel):
    id: str
    item_sku: str
    item_name: str
    current_demand: int
    forecasted_demand: int
    trend: str
    period: str

class BacklogItem(BaseModel):
    id: str
    order_id: str
    item_sku: str
    item_name: str
    quantity_needed: int
    quantity_available: int
    days_delayed: int
    priority: str
    has_purchase_order: Optional[bool] = False

class PurchaseOrder(BaseModel):
    id: str
    backlog_item_id: str
    supplier_name: str
    quantity: int
    unit_cost: float
    expected_delivery_date: str
    status: str
    created_date: str
    notes: Optional[str] = None

class CreatePurchaseOrderRequest(BaseModel):
    backlog_item_id: str
    supplier_name: str
    quantity: int
    unit_cost: float
    expected_delivery_date: str
    notes: Optional[str] = None

# API endpoints
@app.get("/")
def root():
    return {"message": "Factory Inventory Management System API", "version": "1.0.0"}

@app.get("/api/inventory", response_model=List[InventoryItem])
def get_inventory(
    warehouse: Optional[str] = None,
    category: Optional[str] = None
):
    """Get all inventory items with optional filtering"""
    return apply_filters(inventory_items, warehouse, category)

@app.get("/api/inventory/{item_id}", response_model=InventoryItem)
def get_inventory_item(item_id: str):
    """Get a specific inventory item"""
    item = next((item for item in inventory_items if item["id"] == item_id), None)
    if not item:
        raise HTTPException(status_code=404, detail="Item not found")
    return item

@app.get("/api/orders", response_model=List[Order])
def get_orders(
    warehouse: Optional[str] = None,
    category: Optional[str] = None,
    status: Optional[str] = None,
    month: Optional[str] = None
):
    """Get all orders with optional filtering"""
    filtered_orders = apply_filters(orders, warehouse, category, status)
    filtered_orders = filter_by_month(filtered_orders, month)
    return filtered_orders

@app.get("/api/orders/{order_id}", response_model=Order)
def get_order(order_id: str):
    """Get a specific order"""
    order = next((order for order in orders if order["id"] == order_id), None)
    if not order:
        raise HTTPException(status_code=404, detail="Order not found")
    return order

@app.get("/api/demand", response_model=List[DemandForecast])
def get_demand_forecasts():
    """Get demand forecasts"""
    return demand_forecasts

@app.get("/api/backlog", response_model=List[BacklogItem])
def get_backlog():
    """Get backlog items with purchase order status"""
    # Add has_purchase_order flag to each backlog item
    result = []
    for item in backlog_items:
        item_dict = dict(item)
        # Check if this backlog item has a purchase order
        has_po = any(po["backlog_item_id"] == item["id"] for po in purchase_orders)
        item_dict["has_purchase_order"] = has_po
        result.append(item_dict)
    return result

@app.get("/api/dashboard/summary")
def get_dashboard_summary(
    warehouse: Optional[str] = None,
    category: Optional[str] = None,
    status: Optional[str] = None,
    month: Optional[str] = None
):
    """Get summary statistics for dashboard with optional filtering"""
    # Filter inventory
    filtered_inventory = apply_filters(inventory_items, warehouse, category)

    # Filter orders
    filtered_orders = apply_filters(orders, warehouse, category, status)
    filtered_orders = filter_by_month(filtered_orders, month)

    total_inventory_value = sum(item["quantity_on_hand"] * item["unit_cost"] for item in filtered_inventory)
    low_stock_items = len([item for item in filtered_inventory if item["quantity_on_hand"] <= item["reorder_point"]])
    pending_orders = len([order for order in filtered_orders if order["status"] in ["Processing", "Backordered"]])
    total_backlog_items = len(backlog_items)

    return {
        "total_inventory_value": round(total_inventory_value, 2),
        "low_stock_items": low_stock_items,
        "pending_orders": pending_orders,
        "total_backlog_items": total_backlog_items,
        "total_orders_value": sum(order["total_value"] for order in filtered_orders)
    }

@app.get("/api/spending/summary")
def get_spending_summary():
    """Get spending summary statistics"""
    return spending_summary

@app.get("/api/spending/monthly")
def get_monthly_spending():
    """Get monthly spending breakdown"""
    return monthly_spending

@app.get("/api/spending/categories")
def get_category_spending():
    """Get spending by category"""
    return category_spending

@app.get("/api/spending/transactions")
def get_recent_transactions():
    """Get recent transactions"""
    return recent_transactions

@app.get("/api/reports/quarterly")
def get_quarterly_reports(
    warehouse: Optional[str] = None,
    category: Optional[str] = None,
    status: Optional[str] = None
):
    """Get quarterly performance reports with optional filtering"""
    filtered = apply_filters(orders, warehouse, category, status)
    quarters = {}

    for order in filtered:
        order_date = order.get('order_date', '')
        # Determine quarter
        if '2025-01' in order_date or '2025-02' in order_date or '2025-03' in order_date:
            quarter = 'Q1-2025'
        elif '2025-04' in order_date or '2025-05' in order_date or '2025-06' in order_date:
            quarter = 'Q2-2025'
        elif '2025-07' in order_date or '2025-08' in order_date or '2025-09' in order_date:
            quarter = 'Q3-2025'
        elif '2025-10' in order_date or '2025-11' in order_date or '2025-12' in order_date:
            quarter = 'Q4-2025'
        else:
            continue

        if quarter not in quarters:
            quarters[quarter] = {
                'quarter': quarter,
                'total_orders': 0,
                'total_revenue': 0,
                'delivered_orders': 0,
                'avg_order_value': 0
            }

        quarters[quarter]['total_orders'] += 1
        quarters[quarter]['total_revenue'] += order.get('total_value', 0)
        if order.get('status') == 'Delivered':
            quarters[quarter]['delivered_orders'] += 1

    # Calculate averages and fulfillment rate
    result = []
    for q, data in quarters.items():
        if data['total_orders'] > 0:
            data['avg_order_value'] = round(data['total_revenue'] / data['total_orders'], 2)
            data['fulfillment_rate'] = round((data['delivered_orders'] / data['total_orders']) * 100, 1)
        result.append(data)

    # Sort by quarter
    result.sort(key=lambda x: x['quarter'])
    return result

@app.get("/api/reports/monthly-trends")
def get_monthly_trends(
    warehouse: Optional[str] = None,
    category: Optional[str] = None,
    status: Optional[str] = None
):
    """Get month-over-month trends with optional filtering"""
    filtered = apply_filters(orders, warehouse, category, status)
    months = {}

    for order in filtered:
        order_date = order.get('order_date', '')
        if not order_date:
            continue

        # Extract month (format: YYYY-MM-DD)
        month = order_date[:7]  # Gets YYYY-MM

        if month not in months:
            months[month] = {
                'month': month,
                'order_count': 0,
                'revenue': 0,
                'delivered_count': 0
            }

        months[month]['order_count'] += 1
        months[month]['revenue'] += order.get('total_value', 0)
        if order.get('status') == 'Delivered':
            months[month]['delivered_count'] += 1

    # Convert to list and sort
    result = list(months.values())
    result.sort(key=lambda x: x['month'])
    return result


# Restocking feature: per-category lead times (days) used to compute expected delivery
CATEGORY_LEAD_TIMES = {
    'Circuit Boards': 7,
    'Sensors': 5,
    'Actuators': 10,
    'Controllers': 12,
    'Power Supplies': 8,
}

# Fallback cost/category for demand SKUs that don't exist in inventory.json.
# Most demand_forecasts.json SKUs (WDG-*, BRG-*, etc.) are not in inventory,
# so we infer category from SKU prefix and assign a mock unit cost.
DEMAND_SKU_FALLBACK = {
    'WDG': {'category': 'Actuators', 'unit_cost': 42.50},
    'BRG': {'category': 'Actuators', 'unit_cost': 18.75},
    'GSK': {'category': 'Sensors', 'unit_cost': 12.30},
    'MTR': {'category': 'Actuators', 'unit_cost': 95.00},
    'FLT': {'category': 'Sensors', 'unit_cost': 28.40},
    'VLV': {'category': 'Actuators', 'unit_cost': 67.80},
    'SNR': {'category': 'Sensors', 'unit_cost': 34.20},
    'CTL': {'category': 'Controllers', 'unit_cost': 120.00},
}

def _lookup_demand_item_cost(sku: str):
    """Resolve (category, unit_cost) for a demand SKU, preferring inventory then falling back to prefix map."""
    inv_match = next((i for i in inventory_items if i['sku'] == sku), None)
    if inv_match:
        return inv_match['category'], inv_match['unit_cost']
    prefix = sku.split('-')[0]
    fallback = DEMAND_SKU_FALLBACK.get(prefix, {'category': 'Actuators', 'unit_cost': 45.00})
    return fallback['category'], fallback['unit_cost']


class RestockRecommendation(BaseModel):
    sku: str
    name: str
    category: str
    shortfall: int
    recommended_quantity: int
    unit_cost: float
    line_total: float
    lead_time_days: int


class RestockRecommendationResponse(BaseModel):
    budget: float
    recommendations: List[RestockRecommendation]
    total_cost: float
    remaining_budget: float


class RestockOrderItem(BaseModel):
    sku: str
    name: str
    quantity: int
    unit_price: float
    category: str
    lead_time_days: int


class PlaceRestockOrderRequest(BaseModel):
    items: List[RestockOrderItem]


@app.get("/api/restocking/recommendations", response_model=RestockRecommendationResponse)
def get_restocking_recommendations(budget: float):
    """Recommend items to restock within a budget, prioritized by largest demand shortfall."""
    candidates = []
    for d in demand_forecasts:
        shortfall = d['forecasted_demand'] - d['current_demand']
        if shortfall <= 0:
            continue
        category, unit_cost = _lookup_demand_item_cost(d['item_sku'])
        candidates.append({
            'sku': d['item_sku'],
            'name': d['item_name'],
            'category': category,
            'shortfall': shortfall,
            'unit_cost': unit_cost,
            'lead_time_days': CATEGORY_LEAD_TIMES.get(category, 7),
        })

    # Largest shortfall first — greedy fill until budget exhausted
    candidates.sort(key=lambda c: c['shortfall'], reverse=True)

    recommendations = []
    remaining = budget
    for c in candidates:
        full_cost = c['shortfall'] * c['unit_cost']
        if full_cost <= remaining:
            qty = c['shortfall']
            line_total = full_cost
        elif remaining >= c['unit_cost']:
            # Partial fill: buy as many units as remaining budget allows
            qty = int(remaining // c['unit_cost'])
            line_total = qty * c['unit_cost']
        else:
            continue
        recommendations.append({
            **c,
            'recommended_quantity': qty,
            'line_total': round(line_total, 2),
        })
        remaining -= line_total

    total_cost = round(sum(r['line_total'] for r in recommendations), 2)
    return {
        'budget': budget,
        'recommendations': recommendations,
        'total_cost': total_cost,
        'remaining_budget': round(budget - total_cost, 2),
    }


@app.post("/api/restocking/order", response_model=Order)
def place_restocking_order(req: PlaceRestockOrderRequest):
    """Create a new Order from restocking items and append it to the in-memory orders list."""
    if not req.items:
        raise HTTPException(status_code=400, detail="At least one item is required")

    from datetime import datetime, timedelta

    # Next ID continues the existing sequence; order_number uses R-prefix to visually distinguish restocks
    next_id = max((int(o['id']) for o in orders if o['id'].isdigit()), default=0) + 1
    restock_count = sum(1 for o in orders if o.get('status') == 'Restocking') + 1

    max_lead = max(i.lead_time_days for i in req.items)
    now = datetime.now()

    order_items = [
        {'sku': i.sku, 'name': i.name, 'quantity': i.quantity, 'unit_price': i.unit_price}
        for i in req.items
    ]
    total_value = round(sum(i.quantity * i.unit_price for i in req.items), 2)

    new_order = {
        'id': str(next_id),
        'order_number': f'ORD-2025-R{restock_count:03d}',
        'customer': 'Internal Restock',
        'items': order_items,
        'status': 'Restocking',
        'warehouse': None,
        'category': req.items[0].category,
        'order_date': now.strftime('%Y-%m-%dT%H:%M:%S'),
        'expected_delivery': (now + timedelta(days=max_lead)).strftime('%Y-%m-%dT%H:%M:%S'),
        'total_value': total_value,
        'actual_delivery': None,
    }

    orders.append(new_order)
    return new_order



# --- Tasks endpoints (frontend was calling these but they didn't exist — 404 on every page load) ---

class Task(BaseModel):
    id: str
    title: str
    priority: str
    dueDate: str
    status: str


class CreateTaskRequest(BaseModel):
    title: str
    priority: str
    dueDate: str


# In-memory task store (session-scoped, like orders)
_tasks: list = []
_next_task_id = 1


@app.get("/api/tasks", response_model=List[Task])
def get_tasks():
    """Get all tasks."""
    return _tasks


@app.post("/api/tasks", response_model=Task)
def create_task(req: CreateTaskRequest):
    """Create a new task with status='pending'."""
    global _next_task_id
    task = {
        'id': f't{_next_task_id}',
        'title': req.title,
        'priority': req.priority,
        'dueDate': req.dueDate,
        'status': 'pending',
    }
    _next_task_id += 1
    _tasks.append(task)
    return task


@app.delete("/api/tasks/{task_id}")
def delete_task(task_id: str):
    """Delete a task by id."""
    idx = next((i for i, t in enumerate(_tasks) if t['id'] == task_id), None)
    if idx is None:
        raise HTTPException(status_code=404, detail="Task not found")
    _tasks.pop(idx)
    return {"deleted": task_id}


@app.patch("/api/tasks/{task_id}", response_model=Task)
def toggle_task(task_id: str):
    """Toggle a task between pending and completed."""
    task = next((t for t in _tasks if t['id'] == task_id), None)
    if not task:
        raise HTTPException(status_code=404, detail="Task not found")
    task['status'] = 'completed' if task['status'] == 'pending' else 'pending'
    return task


# --- Purchase order endpoints (models + data existed, api.js called them, but no routes) ---

@app.get("/api/purchase-orders/{backlog_item_id}", response_model=PurchaseOrder)
def get_purchase_order_by_backlog_item(backlog_item_id: str):
    """Get the purchase order for a given backlog item."""
    po = next((p for p in purchase_orders if p['backlog_item_id'] == backlog_item_id), None)
    if not po:
        raise HTTPException(status_code=404, detail="No purchase order found for this backlog item")
    return po


@app.post("/api/purchase-orders", response_model=PurchaseOrder)
def create_purchase_order(req: CreatePurchaseOrderRequest):
    """Create a new purchase order for a backlog item."""
    from datetime import datetime
    new_po = {
        'id': f'PO-{len(purchase_orders) + 1:04d}',
        'backlog_item_id': req.backlog_item_id,
        'supplier_name': req.supplier_name,
        'quantity': req.quantity,
        'unit_cost': req.unit_cost,
        'expected_delivery_date': req.expected_delivery_date,
        'status': 'Ordered',
        'created_date': datetime.now().strftime('%Y-%m-%d'),
        'notes': req.notes,
    }
    purchase_orders.append(new_po)
    return new_po


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8001)
