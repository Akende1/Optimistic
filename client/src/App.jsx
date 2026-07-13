import { createBrowserRouter, RouterProvider } from 'react-router-dom';
import Layout from './components/Layout';
import Guard from './components/Guard';
import Home from './pages/Home';
import Products from './pages/Products';
import Product from './pages/Product';
import Cart from './pages/Cart';
import Login from './pages/Login';
import Register from './pages/Register';
import Orders from './pages/Orders';
import OrderDetail from './pages/OrderDetail';
import Addresses from './pages/Addresses';
import Checkout from './pages/Checkout';
import Notifications from './pages/Notifications';
import Account from './pages/Account';
import VerifyAccount from './pages/VerifyAccount';
import SellerKyc from './pages/SellerKyc';
import SellerTerms from './pages/SellerTerms';
import SellerProducts from './pages/SellerProducts';
import SellerEarnings from './pages/SellerEarnings';
import Returns from './pages/Returns';
import CourierRegister from './pages/CourierRegister';
import CourierDeliveries from './pages/CourierDeliveries';
import PasswordReset from './pages/PasswordReset';
import Payment from './pages/Payment';
import ProductEdit from './pages/ProductEdit';
import FulfillmentDetail from './pages/FulfillmentDetail';
import SellerProfile from './pages/SellerProfile';
import CourierProfile from './pages/CourierProfile';
import CourierEarnings from './pages/CourierEarnings';
import SystemState from './pages/SystemState';
import SellerStore from './pages/SellerStore';
import SavedDiscovery from './pages/SavedDiscovery';
import Rfqs from './pages/Rfqs';
import PurchaseOrderCheckout from './pages/PurchaseOrderCheckout';
import Legal from './pages/Legal';
import Placeholder from './pages/Placeholder';
import { Seller } from './pages/RoleDashboard';

const protect = (node, roles) => <Guard roles={roles}>{node}</Guard>;
const router = createBrowserRouter([{ path: '/', element: <Layout />, children: [
  { index: true, element: <Home /> }, { path: 'products', element: <Products /> },
  { path: 'products/:id', element: <Product /> }, { path: 'cart', element: <Cart /> },
  { path: 'sellers/:id', element: <SellerStore /> },
  { path: 'login', element: <Login /> }, { path: 'register', element: <Register /> }, { path: 'password-reset', element: <PasswordReset /> }, { path: 'courier/register', element: <CourierRegister /> },
  { path: 'legal/:document', element: <Legal /> }, { path: 'verify', element: protect(<VerifyAccount />) },
  { path: 'checkout', element: protect(<Checkout />, ['BUYER']) }, { path: 'orders', element: protect(<Orders />, ['BUYER']) },
  { path: 'checkout/purchase-order', element: protect(<PurchaseOrderCheckout />, ['BUYER']) }, { path: 'wishlist', element: protect(<SavedDiscovery mode="wishlist" />, ['BUYER']) }, { path: 'recently-viewed', element: <SavedDiscovery mode="recent" /> },
  { path: 'orders/:id', element: protect(<OrderDetail />, ['BUYER']) }, { path: 'addresses', element: protect(<Addresses />, ['BUYER']) },
  { path: 'orders/:id/payment', element: protect(<Payment />, ['BUYER']) },
  { path: 'notifications', element: protect(<Notifications />) }, { path: 'account', element: protect(<Account />) },
  { path: 'rfqs', element: protect(<Rfqs />) },
  { path: 'seller', element: protect(<Seller />, ['SELLER']) }, { path: 'seller/terms', element: protect(<SellerTerms />, ['SELLER']) },
  { path: 'seller/kyc', element: protect(<SellerKyc />, ['SELLER']) }, { path: 'seller/products', element: protect(<SellerProducts />, ['SELLER']) },
  { path: 'seller/earnings', element: protect(<SellerEarnings />, ['SELLER']) }, { path: 'seller/returns', element: protect(<Returns />, ['SELLER']) },
  { path: 'seller/products/:id/edit', element: protect(<ProductEdit />, ['SELLER']) }, { path: 'seller/fulfillments/:id', element: protect(<FulfillmentDetail />, ['SELLER']) }, { path: 'seller/profile', element: protect(<SellerProfile />, ['SELLER']) },
  { path: 'returns', element: protect(<Returns />) }, { path: 'courier', element: protect(<CourierDeliveries />, ['COURIER']) }, { path: 'courier/profile', element: protect(<CourierProfile />, ['COURIER']) }, { path: 'courier/earnings', element: protect(<CourierEarnings />, ['COURIER']) },
  { path: 'session-expired', element: <SystemState type="session" /> }, { path: 'offline', element: <SystemState type="offline" /> }, { path: 'maintenance', element: <SystemState type="maintenance" /> }, { path: 'error', element: <SystemState type="error" /> }, { path: 'forbidden', element: <SystemState type="forbidden" /> },
  { path: '*', element: <SystemState type="missing" /> },
] }]);

export default function App() { return <RouterProvider router={router} />; }
