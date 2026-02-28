# 🎯 OPTIMISTIC ROLE WORKFLOWS — Complete Separation

**Last Updated:** February 26, 2026  
**Status:** Production Ready ✅

---

## 🧠 Philosophy

> **"Each role sees only what moves their world forward."**

- **Customer:** *"Can I trust this?"*
- **Seller:** *"Can I earn consistently?"*
- **Admin:** *"Is the system healthy?"*

---

## 👤 CUSTOMER (BUYER) WORKFLOW

### Mental Model
*Safe, guided, in control. Shopping with confidence.*

### Pages & Features

#### 🏠 **Home** (`index.html`)
**Purpose:** Discovery & trust-building  
**What they see:**
- Search bar (products, shops, categories)
- Categories grid
- Featured products carousel
- "Trusted sellers" section
- Deals/promotions banners
- Recently viewed items

**Actions:**
- Click category → Browse products
- Click product → View details
- Search → Find products

---

#### 🛍️ **Products** (`products.html`)
**Purpose:** Browse & filter product catalog  
**What they see:**
- Product grid with images, prices, ratings
- Category filters (Electronics, Fashion, Home, etc.)
- Price range slider
- Search bar
- Sort options (Price, Newest, Popular, Rating)
- Pagination

**Actions:**
- Click product → View detail page
- Filter by category
- Filter by price range
- Add to cart (quick action)
- Add to wishlist (❤️ icon)

---

#### 📦 **Product Detail** (`product-detail.html`)
**Purpose:** Make informed purchase decision  
**What they see:**
- Product images gallery (zoom, swipe)
- **Price + availability**
- **Delivery cost calculator** (based on province)
- **Delivery ETA** (estimated days)
- **Seller card:**
  - Seller name
  - Trust score (⭐ rating)
  - Verified badge (if verified)
  - "Visit Store" link
- **Reviews & ratings:**
  - Overall rating
  - Review count
  - Individual reviews with photos
  - Filter by star rating
- **Escrow assurance badge:**
  - "💰 Pay safely. Funds released on delivery."
  - Trust message: "Your money is protected until you receive your order"
- Product description
- Specifications
- Return policy

**Actions:**
- Select quantity
- Add to cart
- Buy now (direct checkout)
- Add to wishlist
- Contact seller
- Share product
- Report product (if suspicious)

---

#### 🛒 **Shopping Cart** (`cart.html`)
**Purpose:** Review & modify order before checkout  
**What they see:**
- Cart items list with:
  - Product image, name, price
  - Quantity selector (+/-)
  - Remove button
  - Subtotal per item
- **Cost breakdown:**
  - Items total
  - Delivery cost (per seller if multiple)
  - Platform fee (if applicable)
  - **TOTAL ZMW**
- Escrow badge reminder
- "Continue shopping" link

**Actions:**
- Update quantities
- Remove items
- Add promo code
- Proceed to checkout
- Save for later

---

#### 💳 **Checkout** (`checkout.html`)
**Purpose:** Complete purchase with confidence  
**What they see:**
- **Order summary** (items, quantities, prices)
- **Delivery address form:**
  - Province selector (Lusaka, Copperbelt, etc.)
  - Street address, district
  - Phone number
  - Delivery instructions
- **Payment method selection:**
  - Mobile money (MTN, Airtel, Zamtel)
  - Card payment
  - Cash on delivery (COD)
- **Cost breakdown:**
  - Items: K 250.00
  - Delivery: K 50.00
  - Total: K 300.00
- **Escrow protection badge**
- Terms & conditions checkbox
- **Place Order button** (primary CTA)

**Actions:**
- Fill delivery details
- Select payment method
- Apply promo code
- Review order
- **Confirm & Pay**

**After Order:**
- Redirect to order confirmation page
- Show order number
- Show payment instructions (if mobile money)
- Email/SMS confirmation

---

#### 📋 **My Orders** (`orders.html`)
**Purpose:** Track all purchases & deliveries  
**What they see:**
- **Orders list** (newest first)
- **Each order card shows:**
  - Order number (#ORD-12345)
  - Date placed
  - Order status badge:
    - ⏳ PENDING (Waiting seller confirmation)
    - ✅ CONFIRMED (Seller accepted)
    - 📦 SHIPPED (Out for delivery)
    - 🚚 IN_TRANSIT (With courier)
    - ✅ DELIVERED (Completed)
    - ❌ CANCELLED/REFUNDED
  - Product thumbnails
  - Total amount
  - Seller name(s)
  - "View Details" button
- **Filter tabs:**
  - All Orders
  - Active (pending, confirmed, shipped, in_transit)
  - Completed
  - Cancelled

**Actions:**
- Click order → View full details
- Track delivery (if shipped)
- Contact seller
- Cancel order (if pending)
- Request refund (if eligible)
- Leave review (after delivery)

---

#### 🚚 **Order Detail** (`order-detail.html`)
**Purpose:** Full order lifecycle visibility  
**What they see:**
- **Order header:**
  - Order number
  - Date placed
  - Current status badge
- **Live status timeline:**
  - ⏳ Order Placed (✓ completed, timestamp)
  - ✅ Seller Confirmed (✓ completed, timestamp)
  - 📦 Packaged (✓ completed, timestamp)
  - 🚚 Out for Delivery (← CURRENT)
  - ✅ Delivered (pending)
- **Delivery tracking:**
  - Courier name & phone
  - Current location (if GPS enabled)
  - Estimated arrival
  - Live updates
- **Items list:**
  - Product images
  - Names, quantities, prices
- **Cost breakdown**
- **Seller information card**
- **Payment details:**
  - Method used
  - Transaction ID
  - Escrow status
- **Delivery address**

**Actions:**
- Contact seller
- Contact courier
- **Raise dispute button** (visible, not hidden):
  - "⚖️ Report Issue"
  - Reasons: Not received, damaged, wrong item, etc.
- Confirm delivery
- Leave review (after delivery)
- Download invoice

---

#### ❤️ **Wishlist** (`wishlist.html`)
**Purpose:** Save products for later  
**What they see:**
- Saved products grid
- Product images, names, prices
- Availability status
- Price change alerts (if price dropped)

**Actions:**
- View product details
- Move to cart
- Remove from wishlist
- Share wishlist

---

#### 👤 **My Dashboard** (`buyer-dashboard.html`)
**Purpose:** Personal command center  
**What they see:**
- Welcome message with name
- **Quick stats:**
  - 📦 Total Orders: 12
  - 🚚 Active Deliveries: 2
  - ❤️ Wishlist Items: 8
  - 💰 Total Spent: K 2,450
- **Order status overview:**
  - Pending: 1
  - Confirmed: 1
  - Shipped: 2
  - Delivered: 8
- **Recent orders** (last 5)
- **Wishlist preview** (top 4 items)
- **Recommended products** (based on history)
- **Quick actions:**
  - Continue Shopping
  - View All Orders
  - Track Deliveries

**Actions:**
- View order details
- Track deliveries
- Browse recommended products

---

#### 🙋 **Profile** (`profile.html`)
**Purpose:** Manage personal account  
**What they see:**
- Profile picture (upload/change)
- Personal details:
  - Full name
  - Email
  - Phone number
- **Saved addresses:**
  - Default delivery address
  - Alternative addresses
  - Add new address
- **Payment preferences:**
  - Saved payment methods
  - Mobile money numbers
- **Reviews written** (history)
- **Account security:**
  - Change password
  - Two-factor authentication
  - Login history
- **Notifications settings:**
  - Email notifications
  - SMS notifications
  - Push notifications

**Actions:**
- Edit personal details
- Add/edit addresses
- Save payment methods
- View review history
- Change password
- Update notification preferences

---

#### 🔔 **Notifications**
**Purpose:** Stay informed about orders  
**What they see:**
- Notification bell icon (navbar)
- Unread count badge
- **Notification types:**
  - 📦 Order confirmed by seller
  - 💰 Payment successful
  - 🚚 Order shipped
  - 🚚 Out for delivery
  - ✅ Order delivered
  - ⚖️ Dispute update
  - ❤️ Wishlist price drop
  - 🎁 New deals/promotions

**Actions:**
- Click to view details
- Mark as read
- View all notifications
- Clear all

---

### ❌ **What Buyers NEVER See:**
- Other buyers' order data
- Seller financial dashboards
- Product approval workflows
- Admin moderation tools
- System logs or backend metrics
- Other users' personal information
- Seller analytics

---

### 🎨 Buyer UX Principles:
1. **Clarity:** Always know order status
2. **Safety:** Escrow badges visible
3. **Speed:** 3 clicks from home to checkout
4. **Trust:** Seller ratings, verified badges
5. **Control:** Easy cancellation, dispute process
6. **Guidance:** Helpful tooltips, delivery ETAs

---

## 🏪 SELLER (SHOP OWNER) WORKFLOW

### Mental Model
*Empowered, not overwhelmed. Run business efficiently.*

### Pages & Features

#### 📊 **Seller Dashboard** (`seller-dashboard-v2.html`)
**Purpose:** Business command center  
**What they see:**
- **Welcome banner:**
  - "Good morning, [Shop Name]!"
  - Verification status badge
  - Shop rating (⭐ 4.8/5)
- **Today's snapshot:**
  - 🛒 New Orders: 5
  - ⏳ Pending Orders: 3
  - 💰 Today's Revenue: K 450
  - 📦 Low Stock Alerts: 2
- **Quick metrics:**
  - Total products: 45
  - Active listings: 42
  - Sold this month: 89
  - Reputation score: 4.8/5
- **Alerts section:**
  - "🔔 New order from Alice K. - Review now"
  - "⚠️ Low stock: Nike Air Max (2 left)"
  - "⚖️ New dispute opened - Order #12345"
- **Recent activity feed:**
  - Order updates
  - Reviews received
  - Product status changes
- **Quick actions:**
  - ➕ Add Product
  - 📦 View Orders
  - 💰 Check Earnings
  - 📊 View Analytics

**Actions:**
- View new orders
- Add product
- Check earnings
- View analytics dashboard

---

#### 📦 **Product Management** (`seller-products-v2.html`)
**Purpose:** Manage inventory & listings  
**What they see:**
- **Products table/grid:**
  - Product image thumbnail
  - Name
  - Price
  - Stock quantity
  - Status badge:
    - 🟢 ACTIVE (visible to buyers)
    - 🟡 PENDING (awaiting admin approval)
    - 🔴 REJECTED (reason shown)
    - ⏸️ PAUSED (seller disabled)
    - 📦 OUT OF STOCK
  - Views count
  - Orders count
  - Actions: Edit, Pause, Delete
- **Filter/sort:**
  - By status
  - By stock level
  - By sales
- **Bulk actions:**
  - Select multiple
  - Pause selected
  - Delete selected

**Actions:**
- Add new product
- Edit product (price, stock, description, images)
- Pause listing (temporarily hide)
- Delete product
- View product analytics
- Upload product images

**Add/Edit Product Flow:**
- Product name
- Category selection
- Price
- Stock quantity
- Description (rich text)
- Images upload (up to 5)
- Specifications (key-value pairs)
- Shipping options
- Return policy
- Submit for approval (if new)

---

#### 🛒 **Orders Management** (`seller-orders-v2.html`)
**Purpose:** Process & fulfill orders  
**What they see:**
- **Orders list:**
  - Order number
  - Customer name (first name + initial)
  - Date placed
  - Status:
    - ⏳ PENDING (needs confirmation)
    - ✅ CONFIRMED (processing)
    - 📦 READY (packed, awaiting courier)
    - 🚚 SHIPPED (handed to courier)
    - ✅ DELIVERED (completed)
    - ❌ CANCELLED
  - Items count
  - Total amount
  - Delivery province
  - Actions: View, Confirm, Ship
- **Filter tabs:**
  - New (need action)
  - Processing
  - Shipped
  - Completed
  - Cancelled
- **Notifications:**
  - "⏰ 3 orders waiting confirmation"

**Actions:**
- View order details
- **Accept order** (PENDING → CONFIRMED)
- **Mark as ready** (CONFIRMED → READY)
- **Assign to courier** / Hand off
- Print packing slip
- Print shipping label
- Contact customer
- Cancel order (with reason)

**Order Detail View:**
- Customer delivery address
- Phone number
- Items ordered
- Payment method
- Delivery partner assigned
- Order timeline
- Customer notes

---

#### 💰 **Earnings** (`seller-earnings-v2.html`)
**Purpose:** Financial transparency  
**What they see:**
- **Revenue dashboard:**
  - Total earnings (lifetime)
  - **Pending balance** (in escrow):
    - K 1,200 (from 8 undelivered orders)
    - "Funds released after delivery confirmation"
  - **Available balance:**
    - K 3,500 (ready to withdraw)
  - This month's earnings: K 2,400
- **Earnings chart:**
  - Daily/weekly/monthly view
  - Revenue trend graph
- **Transactions table:**
  - Date
  - Order number
  - Amount
  - Status (pending/released/withdrawn)
  - Escrow release date
- **Withdrawal history:**
  - Date withdrawn
  - Amount
  - Method (bank, mobile money)
  - Status

**Actions:**
- **Request withdrawal:**
  - Enter amount (from available balance)
  - Select method (bank account, mobile money)
  - Confirm
- View transaction details
- Download financial report (PDF/CSV)
- View escrow breakdown

---

#### ⭐ **Reviews & Reputation** (`seller-profile-v2.html`)
**Purpose:** Build trust, improve service  
**What they see:**
- **Reputation score card:**
  - Overall rating: ⭐ 4.8/5
  - Total reviews: 156
  - 5-star: 120
  - 4-star: 25
  - 3-star: 8
  - 2-star: 2
  - 1-star: 1
- **Performance indicators:**
  - Average delivery time: 3.2 days
  - Response time: <2 hours
  - Order fulfillment rate: 98%
  - Customer satisfaction: 96%
- **Recent reviews:**
  - Customer name (anonymous option)
  - Star rating
  - Comment
  - Product reviewed
  - Date
  - Seller response (if replied)

**Actions:**
- Read reviews
- **Reply to reviews:**
  - Thank happy customers
  - Address complaints professionally
- Flag inappropriate reviews
- View review analytics

---

#### 🏪 **My Store** (`seller-store-v2.html`)
**Purpose:** Customize shop presence  
**What they see:**
- **Store profile:**
  - Shop name
  - Shop logo (upload)
  - Cover photo (upload)
  - Shop description
  - Business address
  - Contact details
  - Social media links
- **Verification status:**
  - ✅ Verified badge (if verified)
  - 🟡 Pending verification
  - Documents required: ID, business license
- **Store settings:**
  - Shop URL: `optimistic.com/shop/[shop-name]`
  - Operating hours
  - Return policy
  - Shipping policy
  - About us section

**Actions:**
- Edit shop details
- Upload logo/cover photo
- Update policies
- Submit verification documents
- View public store page (as buyers see it)

---

#### ⚖️ **Disputes** (`seller-disputes-v2.html`)
**Purpose:** Resolve customer issues  
**What they see:**
- **Disputes list:**
  - Dispute ID
  - Order number
  - Customer name
  - Issue type:
    - Item not received
    - Item damaged
    - Wrong item sent
    - Quality issue
  - Status:
    - 🟡 OPEN (needs response)
    - 🔵 IN_REVIEW (admin investigating)
    - ✅ RESOLVED
    - ❌ CLOSED
  - Date opened
  - Days to respond: 3
  - Actions: View, Respond

**Dispute Detail View:**
- Customer complaint (text + photos)
- Order details
- Evidence timeline
- **Seller response form:**
  - Explanation text
  - Upload evidence (photos, documents)
  - Offer resolution:
    - Full refund
    - Partial refund
    - Replacement
    - Apology/explanation
- Admin messages
- Resolution status

**Actions:**
- Read customer complaint
- Submit response with evidence
- Offer resolution
- Accept admin decision
- View resolution outcome

---

#### 🔔 **Notifications**
**Purpose:** Stay on top of business  
**What they see:**
- **Notification types:**
  - 🛒 New order received
  - 💰 Payment released from escrow
  - ⭐ New review received
  - ⚖️ Dispute opened
  - 📦 Product approved by admin
  - 🔴 Product rejected (with reason)
  - ⚠️ Low stock alert
  - 📊 Weekly sales report
  - 💬 Admin message

**Actions:**
- View notification details
- Mark as read
- Clear all

---

#### 👤 **Profile & Verification** (`seller-profile-v2.html`)
**Purpose:** Account management & trust building  
**What they see:**
- Personal account details
- Shop details (linked)
- **Verification center:**
  - Status: Verified / Pending / Not Verified
  - Required documents:
    - ✅ National ID (uploaded)
    - ✅ Business license (uploaded)
    - 🟡 Proof of address (pending)
  - Upload interface
  - Verification timeline
  - Rejection reasons (if any)
- Business info:
  - Tax ID
  - Bank details (for withdrawals)
  - Mobile money number
- Account security

**Actions:**
- Update personal details
- Upload verification documents
- Update bank/mobile money details
- Change password
- View verification status

---

### ❌ **What Sellers NEVER See:**
- Other sellers' financial data
- Other sellers' product catalogs (private)
- Buyer personal data (full addresses, payment details)
- Admin moderation decisions about other sellers
- Platform-wide financial metrics
- System logs or backend configuration
- Other sellers' analytics

---

### 🎨 Seller UX Principles:
1. **Efficiency:** Dashboard shows what needs action NOW
2. **Transparency:** Always see escrow status, earnings breakdown
3. **Empowerment:** Full control over listings, prices, fulfillment
4. **Fairness:** Clear dispute process, chance to respond
5. **Trust:** Verification badges, reputation scores
6. **Growth:** Analytics show what's working, what's not

---

## 🛡️ SYSTEM ADMIN WORKFLOW

### Mental Model
*See the whole chessboard. Govern, protect, stabilize.*

### Pages & Features

#### 🔧 **Admin Dashboard** (`admin-dashboard-v2.html`)
**Purpose:** Platform health overview  
**What they see:**
- **Platform metrics:**
  - 📊 Total Users: 1,234
    - Buyers: 1,050
    - Sellers: 150
    - Couriers: 34
  - 📦 Total Products: 4,567
    - Active: 4,200
    - Pending approval: 45
    - Rejected: 322
  - 🛒 Total Orders: 8,901
    - Completed: 8,500
    - In progress: 350
    - Cancelled: 51
  - 💰 Platform Revenue: K 45,600
    - This month: K 8,900
    - Commission earned: K 2,340
- **System health indicators:**
  - ✅ API Status: Operational
  - ✅ Database: Healthy
  - ✅ Payment Gateway: Connected
  - ⚠️ Courier API: Slow response
- **Recent activity feed:**
  - New user registrations
  - Seller applications
  - Product submissions
  - Order disputes
  - Error alerts
- **Alerts & flags:**
  - 🔴 5 disputes awaiting review
  - 🟡 45 products awaiting approval
  - ⚠️ 3 sellers with low ratings
  - 🔵 12 new courier applications

**Actions:**
- View detailed metrics
- Review pending items
- Access moderation queue
- View system logs

---

#### 👥 **User Management** (`admin-users-v2.html`)
**Purpose:** Control platform access & roles  
**What they see:**
- **Users table:**
  - User ID
  - Name
  - Email
  - Role badge (BUYER/SELLER/COURIER/ADMIN)
  - Status:
    - ✅ Active
    - 🔴 Suspended
    - ⏸️ Inactive
  - Joined date
  - Last login
  - Orders count (if buyer)
  - Products count (if seller)
  - Verification status
  - Actions: View, Edit, Suspend
- **Filters:**
  - By role
  - By status
  - By verification
  - By join date
- **Search:** By name, email, phone

**User Detail View:**
- Full profile information
- Activity history
- Orders (if buyer)
- Products (if seller)
- Reviews written/received
- Disputes involved in
- Verification documents
- Account flags/warnings
- Admin notes

**Actions:**
- View user details
- **Suspend account:**
  - Reason required
  - Duration (temporary/permanent)
  - Send notification
- Reactivate account
- **Change user role:**
  - Buyer → Seller (approve seller application)
  - Seller → Buyer (demote)
  - Assign admin role
- Verify user
- Reset password
- Add admin notes
- View login history

---

#### 🏪 **Seller Moderation** (`admin-users-v2.html?tab=sellers`)
**Purpose:** Approve & monitor sellers  
**What they see:**
- **Seller applications queue:**
  - Applicant name
  - Shop name
  - Applied date
  - Status: Pending / Approved / Rejected
  - Documents submitted:
    - National ID
    - Business license
    - Proof of address
  - Actions: Review, Approve, Reject

**Review Application Flow:**
- Seller details
- Shop information
- Uploaded documents (view/download)
- Background check results (if integrated)
- Admin notes from previous reviewers
- **Decision options:**
  - ✅ Approve (grant SELLER role + verified badge)
  - 🟡 Request more info
  - ❌ Reject (with reason)

**Seller Performance Monitoring:**
- All sellers list
- Sort by:
  - Reputation score (identify low performers)
  - Total sales
  - Dispute count
  - Response time
- **Actions:**
  - Suspend seller (stop new orders)
  - Remove verified badge
  - Send warning
  - Monitor closely

**Actions:**
- Review seller applications
- Approve/reject sellers
- Verify sellers
- Suspend seller accounts
- View seller performance metrics
- Send seller warnings
- Override trust scores (if abuse detected)

---

#### 📦 **Product & Content Control** (`admin-products-v2.html`)
**Purpose:** Ensure quality & compliance  
**What they see:**
- **Product approval queue:**
  - Product thumbnail
  - Name
  - Seller name
  - Category
  - Price
  - Status: Pending / Approved / Rejected
  - Submitted date
  - Violations flagged (if any)
  - Actions: Review, Approve, Reject

**Product Review Interface:**
- Full product details
- All images
- Description
- Category
- Price
- Seller information
- **Compliance checks:**
  - ✅ No prohibited items (weapons, drugs)
  - ✅ Accurate product description
  - ✅ Appropriate images
  - ✅ Fair pricing (no scams)
  - ✅ Correct category
- **Decision:**
  - ✅ Approve (make public)
  - ❌ Reject:
    - Reason: Prohibited item / Misleading / Low quality / Wrong category
    - Feedback to seller

**All Products View:**
- Filter by status
- Filter by category
- Sort by date, sales, reports
- **Actions:**
  - Feature product (show on homepage)
  - Suspend product (violations)
  - Remove product
  - Edit product (admin override)
  - View product analytics

**Category Management:**
- All categories list
- Add new category
- Edit category
- Set featured categories
- Reorder categories

**Actions:**
- Review pending products
- Approve/reject products
- Feature products on homepage
- Suspend violating products
- Create/edit categories
- Remove fraudulent listings
- Flag suspicious products

---

#### 🛒 **Orders & Logistics** (`admin-orders-v2.html`)
**Purpose:** Monitor order flow & delivery performance  
**What they see:**
- **All orders overview:**
  - Order number
  - Buyer name
  - Seller name
  - Amount
  - Status
  - Payment status
  - Delivery status
  - Date placed
  - Issues flagged
  - Actions: View, Track
- **Filters:**
  - By status
  - By payment method
  - By delivery partner
  - By issue type
  - By date range
- **Delivery performance dashboard:**
  - Average delivery time by province
  - On-time delivery rate: 92%
  - Failed deliveries: 3%
  - Courier performance rankings

**Order Detail View:**
- Full order information
- Buyer & seller details
- Items
- Payment details
- Delivery tracking
- Issue history
- Chat logs (buyer-seller)
- Admin intervention history

**Courier Management:**
- All couriers list
- Performance metrics:
  - Deliveries completed
  - On-time rate
  - Customer ratings
  - Disputes
- Actions:
  - Verify courier
  - Suspend courier
  - Assign delivery
  - View courier routes

**Failed Deliveries & Escalations:**
- Orders stuck in transit
- Customer complaints
- Courier no-shows
- Address issues
- **Admin actions:**
  - Reassign courier
  - Initiate refund
  - Contact parties
  - Escalate to management

**Actions:**
- View all orders
- Monitor delivery performance
- Manage courier accounts
- Verify couriers
- Reassign failed deliveries
- Track stuck orders
- View logistics analytics

---

#### ⚖️ **Disputes & Trust** (`admin-disputes-v2.html`)
**Purpose:** Fair resolution & fraud prevention  
**What they see:**
- **Disputes queue:**
  - Dispute ID
  - Order number
  - Buyer vs Seller
  - Issue type:
    - Not received
    - Damaged item
    - Wrong item
    - Scam/fraud
    - Quality issue
  - Status:
    - 🔴 NEW (needs review)
    - 🟡 INVESTIGATING
    - 🔵 WAITING_RESPONSE
    - ✅ RESOLVED
    - ❌ CLOSED
  - Days open
  - Priority (high/medium/low)
  - Actions: Review, Resolve

**Dispute Resolution Interface:**
- **Case details:**
  - Order information
  - Buyer complaint (text + photos)
  - Seller response (text + photos)
  - Order timeline
  - Payment status
  - Delivery tracking
- **Evidence viewer:**
  - Customer uploaded photos
  - Seller uploaded evidence
  - Chat logs
  - Courier notes
- **Admin investigation tools:**
  - Contact buyer
  - Contact seller
  - Request more evidence
  - Check courier logs
  - View similar disputes
- **Resolution options:**
  - ✅ Full refund to buyer (release escrow)
  - 🔄 Partial refund
  - 📦 Replacement order
  - ❌ Reject dispute (favor seller)
  - ⚠️ Issue warning
  - 🔴 Suspend account (if fraud)
- **Resolution message:**
  - Explain decision
  - Provide evidence summary
  - Next steps

**Fraud & Abuse Prevention:**
- **Pattern detection:**
  - Repeat offenders
  - Suspicious order patterns
  - Multiple disputes from same user
  - Fake reviews
- **Blacklist:**
  - Banned users
  - Blocked emails/phones
  - Suspicious IPs
- **Actions:**
  - Ban user
  - Suspend account
  - Flag for review
  - Report to authorities (if serious)

**Actions:**
- Review disputes
- Contact involved parties
- Request evidence
- Make fair resolution decisions
- Refund orders
- Issue warnings
- Suspend fraudulent accounts
- Blacklist repeat offenders
- View dispute analytics

---

#### 📢 **Notifications & Messaging** (`admin-settings-v2.html`)
**Purpose:** Communicate with users  
**What they see:**
- **System announcements:**
  - Create new announcement
  - Target audience: All / Buyers / Sellers / Couriers
  - Title, message, link
  - Schedule send time
  - View announcement history

**Targeted Messages:**
- Send to specific user
- Send to role group
- Send to users matching criteria:
  - Inactive for 30 days
  - Sellers with low ratings
  - Buyers with abandoned carts

**Notification Templates:**
- Edit email templates
- Edit SMS templates
- Edit push notification templates

**Actions:**
- Send system-wide announcements
- Send targeted messages (seller-only, buyer-only)
- Create notification campaigns
- Edit notification templates

---

#### 📊 **Analytics & Logs** (`admin-reports-v2.html`)
**Purpose:** Data-driven decisions  
**What they see:**
- **Sales analytics:**
  - Daily/weekly/monthly revenue
  - Revenue by category
  - Top-selling products
  - Top-performing sellers
  - Conversion rates
  - Average order value
- **User behavior trends:**
  - New registrations
  - Active users
  - User retention
  - Cart abandonment rate
  - Search trends
- **Platform performance:**
  - Page load times
  - API response times
  - Error rates
  - Uptime percentage
- **Financial reports:**
  - Commission earned
  - Platform revenue
  - Escrow balance
  - Withdrawal requests
- **Export options:**
  - CSV, Excel, PDF
  - Custom date ranges
  - Scheduled reports

**Error Logs:**
- Recent errors
- Error types
- Affected users
- Stack traces
- Actions: View, Resolve, Ignore

**Audit Trails:**
- Admin actions log
- User activities
- System changes
- Security events

**Actions:**
- View analytics dashboards
- Generate custom reports
- Export data
- View error logs
- Monitor audit trails
- Track admin actions

---

#### ⚙️ **System Configuration** (`admin-settings-v2.html`)
**Purpose:** Platform settings & controls  
**What they see:**
- **Payment settings:**
  - Commission rate: 5%
  - Payment gateway credentials
  - Escrow release delay: 3 days after delivery
  - Mobile money provider settings
- **Logistics settings:**
  - Delivery rates by province
  - Courier commission rates
  - Delivery SLA (days)
- **Platform policies:**
  - Return policy (default)
  - Refund policy
  - Cancellation policy
  - Terms of service
  - Privacy policy
- **Feature toggles:**
  - Enable/disable seller registrations
  - Enable/disable reviews
  - Maintenance mode
  - Enable/disable notifications
- **Security settings:**
  - Max login attempts
  - Password requirements
  - Session timeout
  - Two-factor authentication
- **Email/SMS configuration:**
  - SMTP settings
  - SMS gateway API keys
  - Notification preferences

**Maintenance Controls:**
- Enable maintenance mode
- Display maintenance message
- Whitelist admin IPs
- Schedule maintenance window

**Actions:**
- Update commission rates
- Configure payment settings
- Set delivery rates
- Edit platform policies
- Toggle features on/off
- Configure security settings
- Enable maintenance mode
- Update email/SMS settings

---

### ❌ **What Admins NEVER See:**
Admins **do not**:
- Shop as customers (admin accounts cannot place orders)
- Sell products (admin accounts cannot list products)
- Make deliveries (admin accounts are not couriers)

**Admin role is pure governance:**
- View, but not participate
- Moderate, but not transact
- Protect, but stay neutral

---

### 🎨 Admin UX Principles:
1. **Visibility:** See everything, miss nothing critical
2. **Speed:** Quick moderation workflows (approve/reject in 2 clicks)
3. **Fairness:** Show both sides in disputes
4. **Power:** One-click suspend, refund, ban (with safeguards)
5. **Insight:** Analytics show platform health at a glance
6. **Control:** Toggle features, set rates, manage policies

---

## 🔒 ROLE SEPARATION RULES

### Technical Implementation

#### Backend (API Permissions)
```python
# apps/common/permissions.py

class IsBuyer(BasePermission):
    """Only buyers can access"""
    def has_permission(self, request, view):
        return request.user.role == 'BUYER'

class IsSeller(BasePermission):
    """Only sellers can access"""
    def has_permission(self, request, view):
        return request.user.role == 'SELLER'

class IsAdmin(BasePermission):
    """Only admins can access"""
    def has_permission(self, request, view):
        return request.user.role == 'ADMIN'

class IsCourier(BasePermission):
    """Only couriers can access"""
    def has_permission(self, request, view):
        return request.user.role == 'COURIER'
```

#### Frontend (Navigation)
```javascript
// frontend/js/navigation.js

getNavItems(role) {
    const navConfigs = {
        // Buyers see shopping nav
        BUYER: [
            { label: 'Home', href: 'index.html', icon: '🏠' },
            { label: 'Products', href: 'products.html', icon: '🛍️' },
            { label: 'Cart', href: 'cart.html', icon: '🛒' },
            { label: 'Orders', href: 'orders.html', icon: '📦' },
            { label: 'Wishlist', href: 'wishlist.html', icon: '❤️' },
            { label: 'Dashboard', href: 'buyer-dashboard.html', icon: '📊' }
        ],
        
        // Sellers see business nav
        SELLER: [
            { label: 'Dashboard', href: 'seller-dashboard.html', icon: '📊' },
            { label: 'Products', href: 'seller-products-v2.html', icon: '📦' },
            { label: 'Orders', href: 'seller-orders-v2.html', icon: '🛒' },
            { label: 'Earnings', href: 'seller-earnings-v2.html', icon: '💰' },
            { label: 'Store', href: 'seller-store-v2.html', icon: '🏪' }
        ],
        
        // Admins see governance nav
        ADMIN: [
            { label: 'Dashboard', href: 'admin-dashboard-v2.html', icon: '🔧' },
            { label: 'Users', href: 'admin-users-v2.html', icon: '👥' },
            { label: 'Products', href: 'admin-products-v2.html', icon: '📦' },
            { label: 'Orders', href: 'admin-orders-v2.html', icon: '🛒' },
            { label: 'Disputes', href: 'admin-disputes-v2.html', icon: '⚖️' },
            { label: 'Reports', href: 'admin-reports-v2.html', icon: '📊' }
        ]
    };
    
    return navConfigs[role] || navConfigs.guest;
}
```

---

## 🚦 PAGE ACCESS CONTROL

### Public Pages (No Auth Required)
- `index.html` — Home
- `products.html` — Product catalog
- `product-detail.html` — Product details
- `about.html` — About us
- `contact.html` — Contact page
- `login.html` — Login
- `register.html` — Register

### Buyer-Only Pages
- `buyer-dashboard.html` — Buyer dashboard
- `cart.html` — Shopping cart (public, but personalized if logged in)
- `checkout.html` — Checkout (requires buyer login)
- `orders.html` — My orders (requires buyer login)
- `order-detail.html` — Order details (requires buyer login)
- `wishlist.html` — Wishlist (requires buyer login)

### Seller-Only Pages
- `seller-dashboard-v2.html` — Seller dashboard
- `seller-products-v2.html` — Product management
- `seller-orders-v2.html` — Order management
- `seller-earnings-v2.html` — Earnings dashboard
- `seller-store-v2.html` — Store customization
- `seller-disputes-v2.html` — Dispute resolution
- `seller-profile-v2.html` — Seller profile & verification
- `add-product.html` — Add new product

### Admin-Only Pages
- `admin-dashboard-v2.html` — Admin dashboard
- `admin-users-v2.html` — User management
- `admin-products-v2.html` — Product moderation
- `admin-orders-v2.html` — Order monitoring
- `admin-disputes-v2.html` — Dispute resolution
- `admin-finances-v2.html` — Financial overview
- `admin-reports-v2.html` — Analytics & reports
- `admin-settings-v2.html` — System configuration
- `admin-courier-payouts-v2.html` — Courier payments
- `admin-audit-logs-v2.html` — Audit trails

### Shared Pages (All Authenticated Users)
- `profile.html` — User profile (adapts based on role)
- `notifications.html` — Notifications (content filtered by role)

---

## 📋 IMPLEMENTATION CHECKLIST

### ✅ Backend (Already Complete)
- [x] Role-based permissions (IsBuyer, IsSeller, IsAdmin, IsCourier)
- [x] API endpoints with proper permission classes
- [x] User model with role field
- [x] Seller verification workflow
- [x] Order escrow system
- [x] Dispute resolution system
- [x] Notification signals

### 🟡 Frontend (Needs Polish)
- [x] Navigation adapts to user role
- [x] All role-specific pages exist
- [ ] **Add role guards to pages** (redirect if wrong role)
- [ ] **Hide features based on role** (e.g., buyers can't see "Add Product")
- [ ] **Show escrow badges** prominently on buyer pages
- [ ] **Improve seller dashboard** with alerts & quick actions
- [ ] **Enhance admin moderation workflows** (faster approval/rejection)

### 🔴 Testing Required
- [ ] Test buyer journey: register → browse → add to cart → checkout → track order
- [ ] Test seller journey: register → apply → get verified → add product → fulfill order → withdraw earnings
- [ ] Test admin journey: approve seller → approve product → resolve dispute
- [ ] Test role switching: ensure users can't access unauthorized pages

---

## 🎯 NEXT STEPS

### Immediate (Hours)
1. **Add role guards to frontend pages**
   - Check user role on page load
   - Redirect if unauthorized:
     - Buyer trying to access `seller-dashboard.html` → Redirect to `buyer-dashboard.html`
     - Seller trying to access `admin-dashboard-v2.html` → Redirect to `seller-dashboard.html`
     - Anonymous trying to access `checkout.html` → Redirect to `login.html`

2. **Update navigation.js**
   - Ensure nav items match the vision exactly
   - Remove any overlapping/confusing links

3. **Add escrow badges to buyer pages**
   - Product detail page: "💰 Pay safely. Funds released on delivery."
   - Checkout page: "Your money is protected until you receive your order"
   - Order detail page: "Funds held in escrow until delivery confirmed"

### Short-Term (Days)
4. **Enhance seller dashboard alerts**
   - "New orders" badge
   - "Low stock" warnings
   - "Pending disputes" alerts

5. **Improve admin moderation UX**
   - Product approval: Show thumbnail, quick approve/reject buttons
   - Seller verification: Document viewer in same page
   - Dispute resolution: Side-by-side view of buyer/seller evidence

6. **Add guided tours**
   - First-time buyer: "Welcome! Here's how to shop safely"
   - First-time seller: "Let's set up your store"
   - First-time admin: "Platform overview"

### Long-Term (Weeks)
7. **Mobile apps** (separate buyer, seller apps)
8. **Advanced analytics** (ML-powered insights for sellers)
9. **Multi-language support** (English, Bemba, Nyanja)

---

## ✅ SUMMARY

**Vision:** Clean role separation. No overlap. No confusion.

**Customer:** Shop safely, track orders, trust the system.  
**Seller:** Run business, earn money, build reputation.  
**Admin:** Govern platform, resolve disputes, ensure health.

Each role sees **only what answers their core question.**  
That clarity is what separates a marketplace from a mess.

---

**Status:** Workflows defined ✅  
**Next:** Implement role guards + escrow badges + polish dashboards  
**ETA:** 1-2 days to full role separation  

🚀 **Let's make Optimistic the clearest marketplace in Zambia.**
