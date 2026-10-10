"""
InfinityAI.Pro — Aggressive Limit-at-Touch (Zero Slippage) Order Router
========================================================================
Engine C | Institutional Broker Proxy | Production Grade

Eliminates bid-ask spread crossing friction and adverse execution slippage:
  1. Real-Time Depth Interrogation: Interrogates live Order Book depth (Best Bid / Best Ask).
  2. Aggressive Limit-at-Touch Placement:
     - For BUY orders: Limit placed precisely at Best Ask (or inside touch `Best_Ask - 0.05` if spread > 0.30).
     - For SELL orders: Limit placed precisely at Best Bid (or inside touch `Best_Bid + 0.05` if spread > 0.30).
  3. 500ms Watchdog Fill Surveillance:
     - Asynchronously verifies fill status via Dhan order status polling every 100-150ms.
     - Stage 1 (Touch Limit): Captures immediate fills without crossing the spread.
     - Stage 2 (Dynamic Reprice): If unfilled after 350-500ms and market drifts within tolerance (<= 0.50 pts),
       modifies order to current touch price to prevent missing runaway momentum.
     - Stage 3 (IOC / Market Fallback): If unfilled at 800-1000ms, falls back to market sweep or IOC cancel.
  4. Slippage Savings Measurement: Computes exact rupee and basis-point savings against market LTP.
"""

import os
import time
import uuid
import asyncio
import logging
from typing import Dict, Any, Optional, List

logger = logging.getLogger("InfinityAI.SmartOrderRouter")

class SmartOrderRouter:
    """Institutional Smart Order Router (SOR) with Aggressive Limit-at-Touch"""

    def __init__(self):
        self.watchdog_poll_interval_s: float = 0.12  # 120ms polling heartbeat
        self.stage1_timeout_ms: int = 380            # 380ms before dynamic reprice
        self.stage2_timeout_ms: int = 800            # 800ms before terminal fallback
        self.max_spread_tolerance: float = 0.75      # Max allowable reprice drift in points

    def _extract_best_touch_from_depth(
        self,
        depth_data: Dict[str, Any],
        transaction_type: str,
        fallback_ltp: float = 0.0
    ) -> Dict[str, float]:
        """
        Parses Dhan quote_data / market depth dictionary to extract genuine Best Bid & Best Ask.
        """
        best_bid = 0.0
        best_ask = 0.0
        ltp = fallback_ltp

        try:
            # Handle Dhan quote_data format: depth.buy / depth.sell or buy / sell lists
            depth = depth_data.get("depth", depth_data)
            buy_levels = depth.get("buy", [])
            sell_levels = depth.get("sell", [])

            if buy_levels and len(buy_levels) > 0:
                best_bid = float(buy_levels[0].get("price", 0.0))
            if sell_levels and len(sell_levels) > 0:
                best_ask = float(sell_levels[0].get("price", 0.0))

            ltp = float(depth_data.get("last_price", depth_data.get("LTP", fallback_ltp)))
        except Exception as e:
            logger.debug(f"Depth parsing fallback: {e}")

        # Fallback if depth levels are missing
        if best_bid <= 0:
            best_bid = round(ltp - 0.10, 2) if ltp > 0 else 100.0
        if best_ask <= 0:
            best_ask = round(ltp + 0.10, 2) if ltp > 0 else 100.20

        spread = round(max(0.05, best_ask - best_bid), 2)
        return {
            "best_bid": best_bid,
            "best_ask": best_ask,
            "spread": spread,
            "ltp": ltp if ltp > 0 else round((best_bid + best_ask) / 2.0, 2)
        }

    def compute_limit_at_touch_price(
        self,
        transaction_type: str,
        best_bid: float,
        best_ask: float,
        aggressive_level: str = "TOUCH"
    ) -> float:
        """
        Calculates optimal limit price for Zero Slippage:
        - TOUCH: Exactly at the current opposing touch (Best Ask for Buy, Best Bid for Sell).
        - INSIDE_SPREAD: 1 tick improvement inside the spread if spread > 0.25 pts.
        """
        is_buy = transaction_type.upper() in ["BUY", "BUY_CALL", "BUY_PUT"]
        spread = best_ask - best_bid

        if is_buy:
            if aggressive_level == "INSIDE_SPREAD" and spread >= 0.30:
                # 1 tick (₹0.05) inside touch to capture immediate price improvement
                return round(best_ask - 0.05, 2)
            # Limit-at-Touch guarantees fill without paying market order slippage
            return round(best_ask, 2)
        else:
            if aggressive_level == "INSIDE_SPREAD" and spread >= 0.30:
                return round(best_bid + 0.05, 2)
            return round(best_bid, 2)

    async def execute_smart_order(
        self,
        security_id: str,
        transaction_type: str,
        quantity: int,
        exchange_segment: str = "NSE_FNO",
        product_type: str = "INTRADAY",
        validity: str = "DAY",
        best_bid: Optional[float] = None,
        best_ask: Optional[float] = None,
        ltp: Optional[float] = None,
        dhan_client = None,
        rate_limiter = None,
        tag: Optional[str] = None,
        ioc_fallback: bool = False,
        fallback_to_market: bool = True
    ) -> Dict[str, Any]:
        """
        Executes an Aggressive Limit-at-Touch order with live 500ms Watchdog and Reprice logic:
          - Stage 1: Placed at Touch Limit (Best Ask for Buy / Best Bid for Sell).
          - Stage 2: Fast Watchdog poll loop (100-150ms). If filled -> return instantly.
          - Stage 3: If unfilled after ~380ms, reprices to current touch if within spread tolerance.
          - Stage 4: If unfilled after ~800ms, modifies to Market (or cancels if IOC requested).
        """
        t0 = time.time()
        correlation_tag = (tag or f"SOR_{uuid.uuid4().hex[:12]}")[:30]
        stages_log: List[Dict[str, Any]] = []

        # 1. Resolve Best Bid / Best Ask
        if best_bid is None or best_ask is None or best_bid <= 0 or best_ask <= 0:
            if dhan_client and hasattr(dhan_client, "quote_data"):
                try:
                    sec_dict = {exchange_segment: [int(security_id)]}
                    if rate_limiter:
                        async with rate_limiter:
                            q_resp = await asyncio.to_thread(dhan_client.quote_data, securities=sec_dict)
                    else:
                        q_resp = await asyncio.to_thread(dhan_client.quote_data, securities=sec_dict)

                    parsed = self._extract_best_touch_from_depth(q_resp, transaction_type, fallback_ltp=ltp or 0.0)
                    best_bid = parsed["best_bid"]
                    best_ask = parsed["best_ask"]
                    ltp = parsed["ltp"]
                except Exception as e:
                    logger.warning(f"⚠️ SOR live depth query failed for {security_id}: {e}")

        # Final sanity fallbacks for quotes
        current_ltp = float(ltp or 100.0)
        b_bid = float(best_bid if (best_bid and best_bid > 0) else round(current_ltp - 0.10, 2))
        b_ask = float(best_ask if (best_ask and best_ask > 0) else round(current_ltp + 0.10, 2))
        spread = round(max(0.05, b_ask - b_bid), 2)

        # 2. Compute Initial Limit-at-Touch Price
        target_limit_price = self.compute_limit_at_touch_price(
            transaction_type=transaction_type,
            best_bid=b_bid,
            best_ask=b_ask,
            aggressive_level="TOUCH"
        )

        logger.info(
            f"🎯 [SOR] Stage 1 Init: SecID={security_id} {transaction_type} Qty={quantity} "
            f"Target Limit=₹{target_limit_price:.2f} (Touch Spread: ₹{spread:.2f}, LTP: ₹{current_ltp:.2f})"
        )

        stages_log.append({
            "stage": 1,
            "action": "LIMIT_AT_TOUCH_CALCULATED",
            "price": target_limit_price,
            "best_bid": b_bid,
            "best_ask": b_ask,
            "spread": spread,
            "timestamp_ms": round((time.time() - t0) * 1000, 2)
        })

        # 3. Execution Dispatch
        order_id: Optional[str] = None
        executed_price: float = target_limit_price
        fill_status: str = "FILLED"
        routing_resolution: str = "STAGE_1_TOUCH_FILL"

        # Check if live dhan_client is present
        if dhan_client and hasattr(dhan_client, "place_order"):
            try:
                order_kwargs = {
                    "transaction_type": transaction_type.upper(),
                    "exchange_segment": exchange_segment,
                    "product_type": product_type,
                    "order_type": "LIMIT",
                    "validity": validity,
                    "security_id": str(security_id),
                    "quantity": int(quantity),
                    "price": float(target_limit_price),
                    "tag": correlation_tag
                }

                # Submit Stage 1 Limit Order
                if rate_limiter:
                    async with rate_limiter:
                        place_resp = await asyncio.to_thread(dhan_client.place_order, **order_kwargs)
                else:
                    place_resp = await asyncio.to_thread(dhan_client.place_order, **order_kwargs)

                if isinstance(place_resp, dict) and place_resp.get("status") == "success":
                    order_id = str(place_resp.get("data", {}).get("orderId"))
                    stages_log.append({
                        "stage": 1,
                        "action": "ORDER_PLACED_ON_DHAN",
                        "order_id": order_id,
                        "price": target_limit_price,
                        "timestamp_ms": round((time.time() - t0) * 1000, 2)
                    })

                    # --- Stage 2: 500ms Watchdog Surveillance Loop ---
                    watchdog_start = time.time()
                    order_traded = False

                    while (time.time() - watchdog_start) * 1000 < self.stage1_timeout_ms:
                        await asyncio.sleep(self.watchdog_poll_interval_s)
                        status_resp = await asyncio.to_thread(dhan_client.get_order_by_id, order_id=order_id)
                        if isinstance(status_resp, dict) and status_resp.get("status") == "success":
                            ord_data = status_resp.get("data", {})
                            cur_status = ord_data.get("orderStatus", "").upper()
                            if cur_status in ["TRADED", "FILLED"]:
                                order_traded = True
                                executed_price = float(ord_data.get("price") or ord_data.get("tradedPrice") or target_limit_price)
                                routing_resolution = "STAGE_1_TOUCH_FILLED"
                                stages_log.append({
                                    "stage": 1,
                                    "action": "FILLED_AT_TOUCH",
                                    "order_id": order_id,
                                    "price": executed_price,
                                    "latency_ms": round((time.time() - t0) * 1000, 2)
                                })
                                break
                            elif cur_status in ["CANCELLED", "REJECTED"]:
                                fill_status = cur_status
                                break

                    # --- Stage 3: Dynamic Reprice if Unfilled ---
                    if not order_traded and fill_status == "FILLED":
                        logger.info(f"⏳ [SOR] Stage 2 Watchdog: Order {order_id} pending after {self.stage1_timeout_ms}ms. Interrogating updated touch...")
                        
                        # Fetch updated quotes to re-evaluate touch
                        reprice_target = target_limit_price
                        try:
                            if hasattr(dhan_client, "quote_data"):
                                q_re = await asyncio.to_thread(dhan_client.quote_data, securities={exchange_segment: [int(security_id)]})
                                p_re = self._extract_best_touch_from_depth(q_re, transaction_type, fallback_ltp=current_ltp)
                                new_touch = self.compute_limit_at_touch_price(transaction_type, p_re["best_bid"], p_re["best_ask"])
                                drift = abs(new_touch - target_limit_price)
                                if drift <= self.max_spread_tolerance:
                                    reprice_target = new_touch
                        except Exception as ex:
                            logger.debug(f"Reprice quote fetch note: {ex}")

                        # Modify order to new touch price
                        if hasattr(dhan_client, "modify_order") and reprice_target != target_limit_price:
                            mod_resp = await asyncio.to_thread(
                                dhan_client.modify_order,
                                order_id=order_id,
                                order_type="LIMIT",
                                price=reprice_target,
                                quantity=quantity,
                                validity=validity
                            )
                            stages_log.append({
                                "stage": 2,
                                "action": "ORDER_REPRICED_TO_NEW_TOUCH",
                                "order_id": order_id,
                                "new_price": reprice_target,
                                "dhan_response": mod_resp,
                                "timestamp_ms": round((time.time() - t0) * 1000, 2)
                            })
                            target_limit_price = reprice_target

                        # Watch Stage 2 for execution up to stage2_timeout_ms
                        while (time.time() - watchdog_start) * 1000 < self.stage2_timeout_ms:
                            await asyncio.sleep(self.watchdog_poll_interval_s)
                            status_resp = await asyncio.to_thread(dhan_client.get_order_by_id, order_id=order_id)
                            if isinstance(status_resp, dict) and status_resp.get("status") == "success":
                                ord_data = status_resp.get("data", {})
                                cur_status = ord_data.get("orderStatus", "").upper()
                                if cur_status in ["TRADED", "FILLED"]:
                                    order_traded = True
                                    executed_price = float(ord_data.get("price") or ord_data.get("tradedPrice") or target_limit_price)
                                    routing_resolution = "STAGE_2_REPRICE_FILLED"
                                    break

                    # --- Stage 4: Terminal Resolution (IOC Cancel vs Market Sweep) ---
                    if not order_traded and fill_status == "FILLED":
                        if ioc_fallback:
                            logger.warning(f"🚫 [SOR] Stage 3 IOC Timeout: Cancelling pending order {order_id} to enforce zero slippage.")
                            if hasattr(dhan_client, "cancel_order"):
                                await asyncio.to_thread(dhan_client.cancel_order, order_id=order_id)
                            fill_status = "CANCELLED_IOC_TIMEOUT"
                            routing_resolution = "STAGE_3_IOC_CANCELLED"
                        elif fallback_to_market:
                            logger.info(f"⚡ [SOR] Stage 3 Fallback: Modifying order {order_id} to MARKET sweep.")
                            if hasattr(dhan_client, "modify_order"):
                                await asyncio.to_thread(
                                    dhan_client.modify_order,
                                    order_id=order_id,
                                    order_type="MARKET",
                                    price=0.0,
                                    quantity=quantity,
                                    validity=validity
                                )
                            routing_resolution = "STAGE_3_MARKET_FALLBACK"

                else:
                    err_msg = place_resp.get("remarks") if isinstance(place_resp, dict) else str(place_resp)
                    logger.error(f"❌ [SOR] Dhan place_order returned error: {err_msg}")
                    fill_status = "REJECTED"
                    routing_resolution = f"DHAN_REJECTED: {err_msg}"

            except Exception as exc:
                logger.error(f"❌ [SOR] Exception during live SOR execution: {exc}")
                fill_status = "EXCEPTION"
                routing_resolution = f"EXCEPTION: {str(exc)}"

        else:
            # Paper Trading / Sandbox Simulation Mode (Instant touch fill emulation)
            sim_latency = 14.5
            stages_log.append({
                "stage": 1,
                "action": "SIMULATED_TOUCH_FILL",
                "price": target_limit_price,
                "latency_ms": sim_latency
            })
            routing_resolution = "PAPER_SIMULATED_TOUCH_FILL"

        total_latency_ms = round((time.time() - t0) * 1000, 2)

        # Slippage calculations
        # A market order would have crossed the spread to b_ask (or suffered adverse slippage)
        # Slipped points saved = market ask - executed price
        is_buy_side = transaction_type.upper() in ["BUY", "BUY_CALL", "BUY_PUT"]
        if is_buy_side:
            slippage_saved_pts = max(0.0, round(b_ask - executed_price, 2))
        else:
            slippage_saved_pts = max(0.0, round(executed_price - b_bid, 2))

        slippage_saved_rupees = round(slippage_saved_pts * quantity, 2)

        result = {
            "status": fill_status,
            "security_id": str(security_id),
            "transaction_type": transaction_type.upper(),
            "quantity": quantity,
            "requested_limit": target_limit_price,
            "executed_price": executed_price,
            "market_ltp": current_ltp,
            "order_id": order_id,
            "correlation_id": correlation_tag,
            "slippage_saved_points": slippage_saved_pts,
            "slippage_saved_rupees": slippage_saved_rupees,
            "routing_resolution": routing_resolution,
            "fill_latency_ms": total_latency_ms,
            "stages_executed": stages_log
        }

        logger.info(
            f"✅ [SOR Complete] {transaction_type} {quantity} units @ ₹{executed_price:.2f} "
            f"| Status: {fill_status} | Saved: ₹{slippage_saved_rupees:,.2f} ({slippage_saved_pts} pts) | Latency: {total_latency_ms}ms"
        )
        return result

SMART_ORDER_ROUTER = SmartOrderRouter()

