export function createCart({storage, view, key='checkout-cart'}) {
  const state={items:[]}; view.render?.(state); return {add(){return false},setQuantity(){return false},remove(){return false},applyCoupon(){},snapshot(){return state}};
}
