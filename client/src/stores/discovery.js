import { create } from 'zustand';
import { persist } from 'zustand/middleware';
export const useDiscovery=create(persist((set)=>({wishlist:[],recent:[],toggleWishlist:product=>set(state=>({wishlist:state.wishlist.some(row=>row.id===product.id)?state.wishlist.filter(row=>row.id!==product.id):[product,...state.wishlist]})),view:product=>set(state=>({recent:[product,...state.recent.filter(row=>row.id!==product.id)].slice(0,20)}))}),{name:'optimistic-discovery'}));
